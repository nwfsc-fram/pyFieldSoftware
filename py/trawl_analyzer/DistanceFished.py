__author__ = 'Todd.Hay'

# -------------------------------------------------------------------------------
# Name:        DistanceFished.py
# Purpose:     Algorithms for calculating the distance fished for the Trawl Survey
#
# Author:      Todd.Hay
# Email:       Todd.Hay@noaa.gov
#
# Created:     March 2, 2017
# License:     MIT
#-------------------------------------------------------------------------------
import logging
import math
import arrow
import pandas as pd
import numpy as np
import os
import psycopg2.tz

from py.trawl_analyzer.CommonFunctions import CommonFunctions

from ctypes import cdll, c_int, c_double, Structure, POINTER, ARRAY, cast



class LatLon(Structure):
    _fields_ = [("latitude", c_double), ("longitude", c_double)]


class RangeBearing(Structure):
    _fields_ = [("range", c_double), ("bearing", c_double)]


geodll = cdll.LoadLibrary(r"py\trawl_analyzer\GeographicLib.dll")
geodll.sum_test.restype = c_double
geodll.get_lat_lon.restype = POINTER(LatLon)
geodll.get_range_bearing.restype = POINTER(RangeBearing)



# Constants
N_PER_M = 0.000539957            # Nautical Miles Per Meter
SPEED_CHANGE_PCT = 0.04          # Percent Speed Change Threshold

# Technique Types
TECHNIQUES = ["ITI R/B", "ITI $IIGLL", "ITI R/B + Trig", "Catenary", "Vessel + Trig", "GCD + Trig"]
                # "Range Ext + Trig", "Range Ext + Cat + Trig",


class DistanceFished:
    """
    The Distance Fished class performs all of the distance fished calculations for the Trawl Survey.  Algorithms
    typically have two components:  Pre Haulback and Post Haulback.
    """
    def __init__(self):
        super().__init__()
        self._functions = CommonFunctions()
        self._is_depth_valid = False

    def calculate_all_distances_fished(self, tracklines, scope, span, df_depth, df_headrope):
        """
        Method to calculate the distance fished.  We have five techniques from which to choose:

        ---------------------------------------------------------------------------------------------------------
        | Technique     |   PreHaulback                                 | PostHaulback     |   Result           |
        ---------------------------------------------------------------------------------------------------------
        |   A.          |   Vessel + ITI Range / Bearing running mean .....................|  Gear Track        |
        |   B.          |   Vessel + ITI Range / Bearing running mean   | Trig Method      |  Gear Track        |
        |   C.          |   Extrapolated Range from Slope/Distance      | Trig Method      |  Gear Track        |
        |   D.          |   ITI $IIGLL running mean smoothed track line ...................|  Gear Track        |
        |   E.          |   Vessel Great Circle Distance                | Trig Method      |  Distance Fished   |
        |   F.          |   Extrapolated Range from Slope/Distance      | Catenary + Trig  |  Gear Track        |
        ---------------------------------------------------------------------------------------------------------

        So Technique E is never actually directly called, but the distance is just automatically calculated for each
         technique.

        :param tracklines: dict - dictionary containing the tracklines (vessel, iti $iigll, iti range/bearing)
        :param scope: float - scope in meters of the tow line that was let out
        :param span: int - size of window for calculating the running means of the gear track lines
        :param df_depth: pandas DataFrame - contains the depth used for some of the methods
        :param df_headrope: pandas DataFrame - contains the Headrope height.  This combine with the Depth gives the total depth
        :return:
        """

        logging.info(f"starting distance fished calculations")

        gear_tracklines = dict()

        # Gather the waypoint times to use to mask the vessel dataframe, df_vessel
        if "waypoints" not in tracklines["vessel"]:
            logging.error(f"waypoints are missing for some reason, returning from calculating distance fished")
            return None

        waypoints = tracklines["vessel"]["waypoints"]
        try:
            start_haul = arrow.get(waypoints.loc["Start Haul", "best_datetime"]).isoformat() \
                if waypoints.loc["Start Haul", "best_datetime"] is not None and \
                   waypoints.loc["Start Haul", "best_datetime"] is not pd.NaT else \
                    arrow.get(waypoints.loc["Start Haul", "datetime"]).isoformat()
            set_doors = arrow.get(waypoints.loc["Set Doors", "best_datetime"]).isoformat() \
                if waypoints.loc["Set Doors", "best_datetime"] is not None and \
                    waypoints.loc["Set Doors", "best_datetime"] is not pd.NaT else \
                    arrow.get(waypoints.loc["Set Doors", "datetime"]).isoformat()
            doors_fully_out = arrow.get(waypoints.loc["Doors Fully Out", "best_datetime"]).isoformat() \
                if waypoints.loc["Doors Fully Out", "best_datetime"] is not None and \
                   waypoints.loc["Doors Fully Out", "best_datetime"] is not pd.NaT else \
                    arrow.get(waypoints.loc["Doors Fully Out", "datetime"]).isoformat()
            begin_tow = arrow.get(waypoints.loc["Begin Tow", "best_datetime"]).isoformat() \
                if waypoints.loc["Begin Tow", "best_datetime"] is not None and \
                   waypoints.loc["Begin Tow", "best_datetime"] is not pd.NaT else \
                    arrow.get(waypoints.loc["Begin Tow", "datetime"]).isoformat()
            start_haulback = arrow.get(waypoints.loc["Start Haulback", "best_datetime"]).isoformat() \
                if waypoints.loc["Start Haulback", "best_datetime"] is not None and \
                   waypoints.loc["Start Haulback", "best_datetime"] is not pd.NaT else \
                    arrow.get(waypoints.loc["Start Haulback", "datetime"]).isoformat()
            net_off_bottom = arrow.get(waypoints.loc["Net Off Bottom", "best_datetime"]).isoformat() \
                if waypoints.loc["Net Off Bottom", "best_datetime"] is not None and \
                   waypoints.loc["Net Off Bottom", "best_datetime"] is not pd.NaT else \
                    arrow.get(waypoints.loc["Net Off Bottom", "datetime"]).isoformat()
            doors_at_surface = arrow.get(waypoints.loc["Doors At Surface", "best_datetime"]).isoformat() \
                if waypoints.loc["Doors At Surface", "best_datetime"] is not None and \
                   waypoints.loc["Doors At Surface", "best_datetime"] is not pd.NaT else \
                    arrow.get(waypoints.loc["Doors At Surface", "datetime"]).isoformat()
            end_of_haul = arrow.get(waypoints.loc["End Of Haul", "best_datetime"]).isoformat() \
                if waypoints.loc["End Of Haul", "best_datetime"] is not None and \
                   waypoints.loc["End Of Haul", "best_datetime"] is not pd.NaT else \
                    arrow.get(waypoints.loc["End Of Haul", "datetime"]).isoformat()
        except KeyError as ke:
            logging.error(f'Error reading waypoints: {waypoints}  Error = {ke}')
            return None

        """
        Make waypoint adjustments. 
         
        This, in particular, is needed for the catenary line calculation.  For instance, if the begin_tow is adjusted,
        the doors_fully_out time could occur after the begin_tow waypoint, but the doors_fully_out waypoint is 
        a phase change for the catenary line calculation, so it needs to be updated in this case.
        
        """
        if doors_fully_out > begin_tow:
            doors_fully_out = begin_tow

            # TODO Todd Hay - Update the Events Data + Mpl_map points

        logging.info(f"distance fished waypoints:"
                     f"\n\tstart_haul\t\t\t{start_haul}"
                     f"\n\tset_doors\t\t\t{set_doors}"
                     f"\n\tdoors_fully_out\t\t{doors_fully_out}"
                     f"\n\tbegin_tow\t\t\t{begin_tow}"
                     f"\n\tstart_haulback\t\t{start_haulback}"
                     f"\n\tnet_off_bottom\t\t{net_off_bottom}"
                     f"\n\tdoors_at_surface\t{doors_at_surface}")

        # Get and prepare the vessel dataframe
        if "dataframe" not in tracklines["vessel"]:
            logging.error("Vessel trackline was not loaded successfully, stopping calculation")
            return

        df_vessel = tracklines["vessel"]["dataframe"]                                   # Used for Trig Method
        df_vessel.drop_duplicates(subset=['times'], keep="first", inplace=True)         # Required as headings are at 4 Hz

        # TODO Todd Hay - Is this bearing correction even correct?  I'm not convinced !!!!!!! ******* XXXXXX
        df_vessel["bearing"] = df_vessel.apply(
            lambda x: (x["track made good"] - 180)  # Calculate the net bearing from vessel heading
            if (x["track made good"] - 180) >= 0 else x["track made good"] + 180, axis=1)  # Create Bearing

        logging.info(f"\tVESSEL track data, in distance fished, start/end: {df_vessel.iloc[0]} > {df_vessel.iloc[-1]}")

        # Mask out invalid values
        vessel_mask = ((~df_vessel["latitude_invalid"]) & (~df_vessel["longitude_invalid"]))
        df_vessel = df_vessel.loc[vessel_mask]

        logging.info(f"\tVESSEL track data, in distance fished, start/end: {df_vessel.iloc[0]} > {df_vessel.iloc[-1]}")

        logging.info(f"df_vessel size before depth merger: {len(df_vessel)}")
        logging.info(f"df_vessel: {df_vessel.iloc[0]}")
        logging.info(f"df_vessel: {df_vessel.iloc[-1]}")
        logging.info(f"before depth merger: start df_vessel: {df_vessel['times'].iloc[0]} >>> end df_vessel: {df_vessel['times'].iloc[-1]}")
        logging.info(f"before depth merger: start df_depth: {df_depth['times'].iloc[0]} >>> end df_depth: {df_depth['times'].iloc[-1]}")


        if isinstance(df_depth, pd.DataFrame) and not df_depth.empty:
            self._is_depth_valid, df_vessel = self.create_vessel_depth_dataframe(df_vessel=df_vessel, df_depth=df_depth,
                                                                      begin_tow=begin_tow,
                                                                      net_off_bottom=net_off_bottom,
                                                                      doors_at_surface=doors_at_surface)
            df_vessel.drop_duplicates(subset=['times'], keep="first", inplace=True)         #

        else:
            logging.info(f"depth is invalid ...")
            logging.info(f"df_depth = {df_depth}")

        logging.info(f"after depth merger: start df_vessel: {df_vessel['times'].iloc[0]} >>> end df_vessel: {df_vessel['times'].iloc[-1]}")

        logging.info(f"begin_tow: {begin_tow} >>> net_off_bottom: {net_off_bottom}")
        logging.info(f"vessel points size: {len(df_vessel)}")

        padding = math.floor(span / 2)

        logging.info(f"scope: {scope}")
        logging.info(f"span: {span}")
        logging.info(f"padding: {padding}")

        # Iterate through each of the techniques, creating the gear trackline and calculating the distance fished for it
        for technique in TECHNIQUES:

            logging.info(f"\n\nTechnique: {technique}")

            # If scope does not exist for certain techniques, then we need to skip as it is a prerequisite
            if scope is None and ("trig" in technique.lower() or "catenary" in technique.lower()):
                logging.info(f"Scope is null, so cannot continue with the {technique} technique.")
                continue

            df_gear = None
            df_pre = None
            distance = None
            speed = None

            # DEPTH NOT REQUIRED
            if technique in ["ITI R/B", "ITI $IIGLL"]:

                if technique.lower() in tracklines:
                    df_trackline = tracklines[technique.lower()]["dataframe"]

                    # Mask out invalid values
                    if technique == "ITI R/B":
                        mask = ((~df_trackline["range_invalid"]) & (~df_trackline["bearing_invalid"]))
                    elif technique == "ITI $IIGLL":
                        mask = ((~df_trackline["latitude_invalid"]) & (~df_trackline["longitude_invalid"]))
                    df_trackline = df_trackline.loc[mask]

                    df_gear = self.create_gearline_by_smoothed_line(df_trackline=df_trackline, span=span)

                    # Calculate the Pre Haulback Speed
                    df_gear.drop_duplicates(subset=["times"], keep="first", inplace=True)
                    mask = (df_gear["times"] >= begin_tow) & (df_gear["times"] < start_haulback)
                    df_pre = df_gear.loc[mask].copy(deep=True)

            # DEPTH NOT REQUIRED
            elif technique == "ITI R/B + Trig":
                if "iti r/b" in tracklines:
                    df_trackline = tracklines["iti r/b"]["dataframe"].copy(deep=True)

                    # Mask out invalid values
                    mask = ((~df_trackline["range_invalid"]) & (~df_trackline["bearing_invalid"]))
                    df_trackline = df_trackline.loc[mask]

                    df_pre = self.create_prehaulback_gearline_by_smoothed_line(df_trackline=df_trackline,
                                                                           doors_fully_out=doors_fully_out,
                                                                           begin_tow=begin_tow,
                                                                           start_haulback=start_haulback,
                                                                           span=span,
                                                                           padding=padding)

            # DEPTH REQUIRED
            elif technique == "Catenary":

                logging.info(f"is_depth_valid = {self._is_depth_valid}")
                if not self._is_depth_valid:
                    continue

                df_gear = self.create_gearline_by_catenary_prior_bearing(df_vessel=df_vessel,
                                                                               start_haul=start_haul,
                                                                               doors_fully_out=doors_fully_out,
                                                                               begin_tow=begin_tow,
                                                                               start_haulback=start_haulback,
                                                                               net_off_bottom=net_off_bottom,
                                                                               doors_at_surface=doors_at_surface,
                                                                               end_of_haul=end_of_haul,
                                                                               padding=padding,
                                                                               scope=scope,
                                                                               span=span)

                # Calculate the Pre Haulback Speed
                # if isinstance(df_gear, pd.DataFrame) and not df_gear.empty:
                #     df_pre = df_gear.loc[(df_gear["times"] >= begin_tow) & (df_gear["times"] <= start_haulback)].copy(deep=True)
                # else:
                #     continue

            # DEPTH NOT REQUIRED
            elif technique == "Vessel + Trig":

                df_pre = self.create_prehaulback_gearline_by_smoothed_vessel(df_vessel=df_vessel,
                                                                             start_haul=start_haul,
                                                                             start_haulback=start_haulback,
                                                                             end_of_haul=end_of_haul,
                                                                             span=span)

            # DEPTH NOT REQUIRED
            elif technique == "GCD + Trig":

                df_pre = self.create_prehaulback_gearline_by_gcd(df_vessel=df_vessel,
                                                                 begin_tow=begin_tow,
                                                                 start_haulback=start_haulback)

            # DEPTH REQUIRED
            if "Trig" in technique:

                if not self._is_depth_valid:
                    continue

                # Create df_gear + calculate Pre Haulback Speed
                if isinstance(df_pre, pd.DataFrame) and not df_pre.empty:

                    df_trig, df_post = self.create_tow_dataframes(df_vessel=df_vessel,
                                                                  df_depth=df_depth,
                                                                  doors_fully_out=doors_fully_out,
                                                                  start_haulback=start_haulback,
                                                                  net_off_bottom=net_off_bottom,
                                                                  doors_at_surface=doors_at_surface,
                                                                  end_of_haul=end_of_haul,
                                                                  padding=padding)

                    df_post = self.create_posthaulback_gearline_by_trig(df_trig=df_trig,
                                                                        df_post=df_post,
                                                                        scope=scope,
                                                                        span=span,
                                                                        padding=padding)

                    if df_post is None:
                        continue

                    # Merge Pre + Post Haulback into df_gear
                    df_gear = df_pre.append(df_post)

                    # Drop duplicates that occur due to the padding at the end of df_pre and beginning of df_post
                    df_gear.drop_duplicates(subset=["times"], keep="first", inplace=True)

                else:

                    continue

            # Clean Gear Trackline, Transfer Waypoints to it, and Calculate Distances
            if isinstance(df_gear, pd.DataFrame) and not df_gear.empty:

                # Drop rows where gear_lat and gear_lon are NA
                df_gear = df_gear.dropna(subset=["gear_lat", "gear_lon"])

                logging.info(f"size of df_gear: {len(df_gear)}")

                # Transfer the Waypoints to the Gear Trackline
                df_gear, gear_waypoints = self.transfer_waypoints_to_gearline(df_vessel=df_vessel,
                                                                              df_gear=df_gear,
                                                                              begin_tow=begin_tow,
                                                                              start_haulback=start_haulback,
                                                                              net_off_bottom=net_off_bottom)


                logging.info(f"size of df_gear after transferring waypoints: {len(df_gear)}")

                # Calculate the segment distances between all of the points in df_gear from Begin Tow to Net Off Bottom
                pre_mask = (df_gear["times"] >= begin_tow) & (df_gear["times"] <= start_haulback)
                post_mask = (df_gear["times"] >= start_haulback) & (df_gear["times"] <= net_off_bottom)
                df_dist = df_gear.copy(deep=True)
                df_dist = df_dist.rename(columns={"gear_lat": "lat1", "gear_lon": "lon1"})
                df_dist["lat2"] = df_dist["lat1"].shift()
                df_dist["lon2"] = df_dist["lon1"].shift()
                df_dist["dist"] = df_dist.apply(lambda x: self._functions.get_distance(x["lat1"], x["lon1"],
                                                                                       x["lat2"], x["lon2"]), axis=1)

                distance_pre_M = df_dist.loc[pre_mask, "dist"].sum()
                distance_post_M = df_dist.loc[post_mask, "dist"].sum()
                distance_M = distance_pre_M + distance_post_M

                logging.info(f"Distances Fished:\n\tpre: {float(distance_pre_M):.5} M"
                             f"\n\tpost: {float(distance_post_M):.5} M\n\ttotal: {float(distance_M):.5} M")

                distance_pre_N = N_PER_M * distance_pre_M
                time_diff = (arrow.get(start_haulback) - arrow.get(begin_tow)).total_seconds() / 3600
                speed = distance_pre_N / time_diff

                logging.info(f"Pre-Haulback Speed: {speed} kts")

                # Convert from numpy.float64 to regular python floats
                distance_pre_M = float(distance_pre_M) if distance_pre_M else None
                distance_post_M = float(distance_post_M) if distance_post_M else None
                distance_M = float(distance_M) if distance_M else None
                speed = float(speed) if speed else None

                # Do a final mask on df_gear to only have points from start_haul > end_of_haul
                mask = (df_gear["times"] >= start_haul) & (df_gear["times"] <= end_of_haul)
                df_gear = df_gear.loc[mask]

                # Add the track line to our dictionary of all track lines
                gear_tracklines[technique] = {"dataframe": df_gear, "distance_M": distance_M,
                                              "distance_pre_M": distance_pre_M, "distance_post_M": distance_post_M,
                                              "speed": speed, "waypoints": gear_waypoints,
                                              "start_haul": start_haul, "end_of_haul": end_of_haul}

        return gear_tracklines

    def transfer_waypoints_to_gearline(self, df_vessel, df_gear, begin_tow, start_haulback, net_off_bottom):
        """
        Method to plot the gear waypoints on the newly generated gear trackline
        :param df_gear: pandas DataFrame of the gear trackline
        :param begin_tow: arrow date/time
        :param start_haulback: arrow date/time
        :param net_off_bottom: arrow date/time
        :return:
        """
        # logging.info(f"times: BT: {begin_tow}, SH: {start_haulback}, NOB: {net_off_bottom}")

        # Find waypoints whose times are already actualized as points on the df_gear trackline
        tow_waypoints = [begin_tow, start_haulback, net_off_bottom]
        df_waypoints = df_gear.loc[df_gear["times"].isin(tow_waypoints)]

        logging.info(f"VESSEL:\n\tstart time: {df_vessel.iloc[1].loc['times']}\n\tend time: {df_vessel.iloc[-1].loc['times']}")
        logging.info(f"GEAR:\n\tstart time: {df_gear.iloc[1].loc['times']}\n\tend time: {df_gear.iloc[-1].loc['times']}")

        logging.info(f"tow_waypoints: {tow_waypoints}")
        logging.info(f"isin exactly found waypoints: {df_waypoints.loc[:,['times', 'gear_lat', 'gear_lon']]}")

        time_map = {"Begin Tow": begin_tow,
                    "Start Haulback": start_haulback,
                    "Net Off Bottom": net_off_bottom}

        waypoints = dict()
        for idx, wp in df_waypoints.iterrows():
            point_type = None
            for k, v in time_map.items():
                if arrow.get(wp['times']).isoformat() == v:
                    point_type = k
                    break
            if point_type:
                logging.info(f"Transferring waypoint:  Existing point on gear trackline: {point_type}")

                tow_waypoints.remove(time_map[k])
                point_dict = dict()
                point_dict["type"] = point_type
                point_dict["datetime"] = wp["times"]
                point_dict["gear_lat"] = wp["gear_lat"]
                point_dict["gear_lon"] = wp["gear_lon"]
                waypoints[point_type] = point_dict

        # Find placement positions in df_gear for the remaining waypoints whose times are not already in df_gear
        # logging.info(f'df_gear times: {df_gear["times"]}')
        tow_waypoints = [arrow.get(x).datetime for x in tow_waypoints]
        logging.info(f"tow_waypoints in datetime format: {tow_waypoints}")
        idx = df_gear["times"].searchsorted(tow_waypoints)
        logging.info(f"searchsorted interpolated waypoints: {idx}")

        if len(idx) > 0:
            for i, x in enumerate(idx):
                logging.info(f"Transferring waypoint:  Interpolating: {x}")
                if x >= len(df_gear):
                    # Past the end of the line, skipping adding the waypoint
                    continue

                logging.info(f"\t\t{df_gear.iloc[x].index.tolist()[0]} >>> {df_gear['times'].iloc[x-1]} >>> {df_gear['times'].iloc[x]}")

                lat1 = df_gear["gear_lat"].iloc[x - 1]
                lon1 = df_gear["gear_lon"].iloc[x - 1]
                lat2 = df_gear["gear_lat"].iloc[x]
                lon2 = df_gear["gear_lon"].iloc[x]

                # Get the time difference
                end_time = arrow.get(df_gear["times"].iloc[x])
                time_diff = (end_time - arrow.get(df_gear["times"].iloc[x - 1])).total_seconds()

                # Find the distance and bearing between the before and after df_gear points
                dist, bearing = self._functions.get_distance_bearing(lat1=lat1, lon1=lon1, lat2=lat2, lon2=lon2)

                # Calculate the range to the waypoint that is going to be added to df_gear
                wp_time = arrow.get(tow_waypoints[i])
                ratio = (end_time - wp_time).total_seconds() / time_diff
                wp_range = ratio * dist

                # Calculate the lat/lon for the new df_gear point
                wp_lat, wp_lon = self._functions.get_lat_lon(lat1=lat1, lon1=lon1, range=wp_range, bearing=bearing)

                # logging.info(f"\t\tNew waypoint info:  time= {tow_waypoints[i]}, lat= {wp_lat}, lon= {wp_lon}")

                # Plot it
                point_type = None
                for k, v in time_map.items():
                    if wp_time.isoformat() == v:
                        point_type = k
                        break
                if point_type:
                    logging.info(f"\t\tPoint type to transfer: {point_type}")
                    point_dict = dict()
                    point_dict["type"] = point_type
                    point_dict["datetime"] = wp_time.datetime
                    point_dict["gear_lat"] = wp_lat
                    point_dict["gear_lon"] = wp_lon
                    waypoints[point_type] = point_dict

                    # logging.info(f"point_type: {point_type} >>> waypoint: {point_dict}")

                    # Add this newly interpolated point to the df_gear track line
                    # TODO Todd Hay - Hardcoded the temporal offset

                    offset = wp_time.utcoffset()
                    offset = offset.days * 1440 + offset.seconds / 60
                    logging.info(f"offset = {offset}")

                    """
                    Had to adjust the tzinfo to use a psycopg2.tz.FixedOffsetTimezone otherwise it would fail with a 
                    typical arrow-based timezone that was converted to a standard datetime object via .datetime
                    Reference - https://github.com/crsmithdev/arrow/issues/313
                                http://initd.org/psycopg/docs/tz.html
                    """
                    dfdict = {"times": wp_time.replace(tzinfo=psycopg2.tz.FixedOffsetTimezone(offset=offset)).datetime,
                              "gear_lat": wp_lat, "gear_lon": wp_lon}
                    df_gear = df_gear.append(dfdict, ignore_index=True)

            # Reset order the index - need to convert to pandas datetime format and do some timezone conversions to get it to work
            df_gear["times"] = pd.to_datetime(df_gear["times"], utc=True)
            df_gear.set_index("times", drop=False, inplace=True)
            logging.info(f"tzinfo: {df_gear.index.tzinfo}")
            if df_gear.index.tzinfo:
                df_gear.index = df_gear.index.tz_convert("US/Pacific")
            else:
                df_gear.index = df_gear.index.tz_localize("UTC").tz_convert("US/Pacific")
            df_gear.sort_index(inplace=True)
            df_gear.drop(["times"], axis=1, inplace=True)
            df_gear.reset_index(inplace=True)

        return df_gear, waypoints

    def create_vessel_depth_dataframe(self, df_vessel, df_depth, begin_tow, net_off_bottom, doors_at_surface):
        """
        Method to merge the vessel and depth dataframes.  With a solid depth curve, this is easy. However if the
        depth curve stopped abruptly (we see this sometimes with the SBE39) data, then we need to get an average
        of the available depth on bottom and then extrapolate the rest of the curve from that.
        :param df_vessel:
        :param df_depth:
        :return:
        """
        depth_exists = False

        if isinstance(df_depth, pd.DataFrame) and not df_depth.empty:

            depth_mask = (~df_depth["invalid"])
            df_depth = df_depth.loc[depth_mask]

            df_depth = df_depth.rename(columns={"values": "depth"})               # Rename the depth column
            df_depth.drop(["invalid", "id"], axis=1, inplace=True)                # Drop extraneuous df_depth columns

            logging.info(f"size of df_depth: {len(df_depth)}")
            logging.info(f"df_depth col: {df_depth.columns.values}")

            # Round both the depth and vessel dataframes to the nearest second, otherwise they won't merge on microseconds
            df_depth["times"] = df_depth["times"].dt.round('1s')
            df_vessel["times"] = df_vessel["times"].dt.round('1s')
            # s = 200
            # e = s+10
            # logging.info(f"df_depth:\n{df_depth.loc[s:e, 'times']}")
            # s = 142
            # e = s+10
            # logging.info(f"df_vessel:\n{df_vessel.loc[s:e, 'times']}")

            df_vessel = pd.merge(df_vessel, df_depth, how="left", on="times")  # Add depth to vessel

            last_time = arrow.get(df_depth["times"].iloc[-1]).isoformat()
            logging.info(f"last_time = {last_time}, net_off_bottom = {net_off_bottom}")

            if last_time < net_off_bottom:
                # Full depth curve does not exist, piece together an average depth on bottom

                logging.info(f"\n\tbegin_tow: {begin_tow}"
                             f"\n\tnet_off_bottom: {net_off_bottom}")

                s = 0
                e = s+10
                logging.info(f"df_depth beginning\n{df_depth.loc[s:e, 'times']}")

                s = len(df_depth) - 10
                e = s+10
                logging.info(f"df_depth ending\n{df_depth.loc[s:e, 'times']}")

                mask = (df_depth["times"] >= begin_tow) & (df_depth["times"] <= net_off_bottom)
                df_depth_test = df_depth.loc[mask]
                logging.info(f"df_depth size within time on bottom: {len(df_depth_test)}")

                if len(df_depth_test) >= 5:
                    avg_depth = df_depth_test.loc[:, "depth"].mean()

                    # Apply the average bottom depth to the remaining of the on bottom curve
                    mask = (df_vessel["times"] > last_time) & (df_vessel["times"] <= net_off_bottom)
                    df_vessel["depth"].loc[mask] = avg_depth

                    # Apply a linear depth for the remainder of the graph
                    mask = (df_vessel["times"] > net_off_bottom) & (df_vessel["times"] <= doors_at_surface)
                    num_pts = len(df_vessel.loc[mask])
                    rate = avg_depth / num_pts
                    df_vessel["depth"].loc[mask] = [avg_depth - (i+1) * rate for i in range(num_pts)]

                    # path = os.path.expanduser("~/Desktop/df_vessel_depth.csv")
                    # df_vessel.loc[:, ['times', 'latitude', 'longitude', 'track made good', 'depth']].to_csv(path)

                    depth_exists = True
                    df_vessel = df_vessel.dropna(subset=["depth"])  # Drop rows where column values are NA

            else:

                depth_exists = True
                df_vessel = df_vessel.dropna(subset=["depth"])  # Drop rows where column values are NA

        return depth_exists, df_vessel

    def create_tow_dataframes(self, df_vessel, df_depth, doors_fully_out, start_haulback, net_off_bottom, doors_at_surface, end_of_haul, padding):
        """
        Method to create the df_trig and df_post data frames
        :param df_vessel:
        :param start_haulback:
        :param net_off_bottom:
        :param doors_at_surface:
        :param padding:
        :return:
        """

        # Add in the df_depth data if it is valid
        df_depth["times"] = df_depth["times"].dt.round('1s')
        df_vessel["times"] = df_vessel["times"].dt.round('1s')

        if self._is_depth_valid:
            df_vessel = pd.merge(df_vessel, df_depth, how="left", on="times")  # Add depth to vessel
            df_vessel = df_vessel.dropna(subset=["depth"])  # Drop rows where column values are NA
            logging.info(f"vessel and depth successfully merged")

        # Create the df_trig dataframe - from start_haulback to end_of_haul
        trig_method_mask = (df_vessel["times"] >= start_haulback) & (df_vessel["times"] <= end_of_haul)
        df_trig = df_vessel.loc[trig_method_mask]
        logging.info(f"df_trig size: {len(df_trig)}")

        if len(df_trig) > 0:
            start = df_vessel.index.get_loc(df_trig.head(1).index.tolist()[0]) - padding
            end = df_vessel.index.get_loc(df_trig.tail(1).index.tolist()[0])
            df_trig = df_vessel.iloc[start:end].copy(deep=True)
        else:
            logging.info(f"df_trig is zero, skipping masking")

        # Define df_post elements
        post_haulback_mask = (df_vessel["times"] >= start_haulback) & (df_vessel["times"] <= end_of_haul)
        df_post = df_vessel.loc[post_haulback_mask]

        if len(df_post) > 0:
            start = df_vessel.index.get_loc(df_post.head(1).index.tolist()[0]) - padding
            end = df_vessel.index.get_loc(df_post.tail(1).index.tolist()[0])
            df_post = df_vessel.iloc[start:end].copy(deep=True)
        else:
            logging.info(f"df_post is zero, skipping masking")

        return df_trig, df_post

    def calculate_prehaulback_speed(self, technique, df_pre, begin_tow, start_haulback):
        """
        Method to calculate the speed of the prehaulback period, found from df_pre
        :param df_pre:
        :return:
        """
        speed = None
        if technique == "GCD + Trig":
            if len(df_pre) == 2:
                lat1 = df_pre.iloc[0]["gear_lat"]
                lon1 = df_pre.iloc[0]["gear_lon"]
                lat2 = df_pre.iloc[1]["gear_lat"]
                lon2 = df_pre.iloc[1]["gear_lon"]
                distance, bearing = self._functions.get_distance_bearing(lat1=lat1, lon1=lon1, lat2=lat2, lon2=lon2)
                distance_N = N_PER_M * distance
                time_diff = (arrow.get(df_pre.iloc[1]["times"]) - arrow.get(df_pre.iloc[0]["times"])).total_seconds() / 3600
                speed = distance_N / time_diff

        else:
            mask = (df_pre["times"] >= begin_tow) & (df_pre["times"] <= start_haulback)
            df_dist_pre = df_pre.copy(deep=True)
            df_dist_pre = df_dist_pre.rename(columns={"gear_lat": "lat1", "gear_lon": "lon1"})
            df_dist_pre["lat2"] = df_dist_pre["lat1"].shift()
            df_dist_pre["lon2"] = df_dist_pre["lon1"].shift()
            df_dist_pre.loc[mask, "dist"] = df_dist_pre.loc[mask].apply(
                lambda x: self._functions.get_distance(x["lat1"], x["lon1"], x["lat2"], x["lon2"]), axis=1)
            distance = df_dist_pre["dist"].sum()
            distance_N = N_PER_M * distance

            time_diff = (arrow.get(start_haulback) - arrow.get(begin_tow)).total_seconds() / 3600
            speed = distance_N / time_diff

        logging.info(f"Gear PreHaulback Distance, BT > SH: {distance_N:.2} NM")
        logging.info(f"Gear PreHaulback Speed, BT > SH: {speed:.2} kts")

        return speed

    def create_prehaulback_gearline_by_smoothed_vessel(self, df_vessel, start_haul, start_haulback, end_of_haul, span):
        """
        Method to create the df_pre gear trackline from a smoothed vessel trackline
        :param df_vessel:
        :param start_haul:
        :param start_haulback:
        :param end_of_haul:
        :param span:
        :return:
        """
        df_pre = df_vessel.copy(deep=True)
        df_pre.drop_duplicates(subset=['times'], keep="first", inplace=True)  # Required, headings are at 4 Hz
        df_pre.loc[:, "gear_lat"] = df_pre.loc[:, "latitude"]
        df_pre.loc[:, "gear_lon"] = df_pre.loc[:, "longitude"]
        df_pre.loc[:, ["gear_lat", "gear_lon"]] = \
            df_pre.loc[:, ["gear_lat", "gear_lon"]].rolling(window=span, center=True).mean()
        mask = (df_pre["times"] < start_haulback)
        df_pre = df_pre.loc[mask]

        return df_pre

    def create_prehaulback_gearline_by_gcd(self, df_vessel, begin_tow, start_haulback):
        """
        Method to create the df_pre gear trackline from a GCD of the vessel trackline
        :param df_vessel:
        :param begin_tow:
        :param net_off_bottom:
        :return:
        """
        df_pre = df_vessel.copy(deep=True)
        df_pre.drop_duplicates(subset=['times'], keep="first", inplace=True)  # Required, headings are at 4 Hz
        df_pre.loc[:, "gear_lat"] = df_pre.loc[:, "latitude"]
        df_pre.loc[:, "gear_lon"] = df_pre.loc[:, "longitude"]

        # logging.info(f"gcd calc: {begin_tow}, {start_haulback}")
        # logging.info(f"gcd head: {df_pre.head(5)}")
        # logging.info(f"gcd tail: {df_pre.tail(5)}")
        # logging.info(f"index: {df_pre.index.tolist()}")
        # logging.info(f"df_pre size: {len(df_pre)}")

        start_mask = df_pre['times'].isin([begin_tow])
        if len(df_pre.loc[start_mask]) > 0:
            start_rec = df_pre.loc[start_mask]
        else:
            idx = df_pre["times"].searchsorted(begin_tow)
            if idx == len(df_pre):
                if idx > 0:
                    start_rec = df_pre.iloc[idx-1]
                else:
                    # Cannot find a legitimate start_rec
                    return None
            else:
                start_rec = df_pre.iloc[idx]

            # logging.info(f"begin_tow: {begin_tow}")
            # logging.info(f"gcd start idx: {idx}")
            # logging.info(f"start_rec: {start_rec}")

        end_mask = df_pre["times"].isin([start_haulback])
        if len(df_pre.loc[end_mask]) > 0:
            end_rec = df_pre.loc[end_mask]
        else:
            idx = df_pre["times"].searchsorted(start_haulback)
            if idx == len(df_pre):
                if idx > 0:
                    end_rec = df_pre.iloc[idx-1]
                else:
                    return None
            else:
                end_rec = df_pre.iloc[idx]

        df_pre = start_rec.append(end_rec)

        return df_pre

    def create_prehaulback_gearline_by_smoothed_line(self, df_trackline, doors_fully_out, begin_tow, start_haulback, span, padding):
        """
        Method to create a gear trackline using the iti r/b for the prehaulback and the trig method
        for the post haulback
        :param df_trackline: pandas DataFrame
        :param begin_tow: arrow date/time
        :param start_haulback: arrow date/time
        :param span:
        :return:
        """

        # Padding done to ensure that the running mean calculates values at the ending point
        df_trackline.drop_duplicates(subset=["times"], keep="first", inplace=True)
        mask = (df_trackline["times"] >= doors_fully_out) & (df_trackline["times"] < start_haulback)
        df_pre = df_trackline.loc[mask]

        if len(df_pre) == 0:
            return None

        start = df_trackline.index.get_loc(df_pre.head(1).index.tolist()[0]) #- padding  #- 1  # Subtract an extra for waypoint transfer later on
        end = df_trackline.index.get_loc(df_pre.tail(1).index.tolist()[0]) + padding   #+ 1
        df_pre = df_trackline.iloc[start:end].copy(deep=True)

        # df_pre = df_trackline.loc[mask].copy(deep=True)
        df_pre.loc[:, ["latitude", "longitude"]] = \
            df_pre.loc[:, ["latitude", "longitude"]].rolling(window=span, center=True).mean()
        df_pre = df_pre.rename(columns={"latitude": "gear_lat", "longitude": "gear_lon"})

        return df_pre

    def create_posthaulback_gearline_by_trig(self, df_trig, df_post, scope, span, padding):
        """
        Method to calculate the posthaulback gearline using the trig method
        :param df_trig:
        :param df_post:
        :param scope:
        :param span:
        :return:
        """
        # Gather static values for the trig method
        if len(df_trig) < padding+1:
            return None

        time_diff = (df_trig["times"].iloc[-1] - df_trig["times"].iloc[0+padding]).seconds  # Start Haulback to Doors At Surface
        ratio = scope / time_diff                                                   # Ratio of Scope to Time Diff
        trig_end_time = df_trig["times"].iloc[-1]                                   # Time at Doors At Surface

        # Calculate and assign the scope
        df_trig.loc[:, "scope"] = df_trig.apply(lambda x: (trig_end_time - x["times"]).seconds * ratio, axis=1)
        df_post = df_post.assign(scope=df_trig["scope"])

        # path = os.path.expanduser("~/Desktop/df_post_before.csv")
        # df_post.loc[:, ['times', 'latitude', 'longitude', 'a', 'scope', 'depth', 'track made good', 'bearing', 'gear_lat', 'gear_lon']].to_csv(path)

        # Calculate the range from the scope + depth using pythagorean theorem
        df_post.loc[:, "range"] = df_post.apply(lambda x: math.sqrt(x["scope"] ** 2 - x["depth"] ** 2)
                                                if x["scope"] > x["depth"] and x["depth"] >= 0 else None, axis=1)

        # path = os.path.expanduser("~/Desktop/df_post_after.csv")
        # df_post.loc[:, ['times', 'latitude', 'longitude', 'a', 'scope', 'depth', 'range', 'track made good', 'bearing', 'gear_lat', 'gear_lon']].to_csv(path)

        # Check to see if the range values are null or not.  If null, this means that the depth > scope, which can't
        # be true, so discard the trig method in this case if we find such instances
        # mask = (df_post["range"].isnull())
        # df_post = df_post.loc[mask]
        # if len(df_post) > 0:
        #     logging.info(f"Trig method, count where the depth > scope: {len(df_post)}, skipping the trig method")
        #     return None

        # Calculate the gear_lat and gear_lon
        df_post["gear_lat"] = df_post.apply(lambda x: self._functions.get_lat(lat=x["latitude"],
                                                                              lon=x["longitude"],
                                                                              bearing=x["bearing"],
                                                                              range=x["range"]) if x["range"] is not None else None, axis=1)
        df_post["gear_lon"] = df_post.apply(lambda x: self._functions.get_lon(lat=x["latitude"],
                                                                              lon=x["longitude"],
                                                                              bearing=x["bearing"],
                                                                              range=x["range"]) if x["range"] is not None else None, axis=1)

        # Smooth the df_post line using a running mean
        df_post.loc[:, ["gear_lat", "gear_lon"]] = df_post.loc[:, ["gear_lat", "gear_lon"]].rolling(window=span,
                                                                                                    center=True).mean()

        return df_post

    def create_gearline_by_catenary_prior_bearing(self, df_vessel, start_haul, doors_fully_out, begin_tow, start_haulback,
                                    net_off_bottom, doors_at_surface, end_of_haul, padding, scope, span):
        """
        Method to create the catenary gear line using the prior bearing information
        :param df_vessel:
        :param start_haul:
        :param doors_fully_out:
        :param begin_tow:
        :param start_haulback:
        :param net_off_bottom:
        :param doors_at_surface:
        :param end_of_haul:
        :param padding:
        :param scope:
        :param span:
        :param avg_depth:
        :return:
        """
        # Copy the vessel dataframe to the gear dataframe and add in the gear_lat, gear_lon, and range columns
        df_gear = df_vessel.copy(deep=True)
        df_gear.loc[:, "gear_lat"] = df_gear.loc[:, "latitude"]
        df_gear.loc[:, "gear_lon"] = df_gear.loc[:, "longitude"]
        df_gear.loc[:, "range"] = 0

        #################################################################################
        # Get the First Record (or nearest point to it on the vessel track)
        #################################################################################
        initialize_time = start_haul # begin_tow
        mask = (df_gear["times"] == initialize_time)
        record = df_gear.loc[mask]
        if not record.empty:
            record = df_gear.loc[mask].iloc[0]
        else:
            idx = df_gear["times"].searchsorted(initialize_time)
            if idx:
                record = df_gear.iloc[idx[0]-1]
                if record.empty:
                    return
            else:
                if idx == 0:
                    record = df_gear.iloc[0]
                else:
                    return

        # logging.info(f"catenary starting record: {record}")

        #################################################################################
        # Calculate the gear_lat / gear_lon at the starting point - this is passed to the C DLL
        #################################################################################
        track_made_good = record["track made good"]
        bearing = track_made_good - 180 if track_made_good >= 180 else track_made_good + 180
        bearing = track_made_good - 180
        depth = record["depth"]
        if depth > 0:
            a = (scope ** 2 - depth ** 2) / (2 * depth)
            scope_0 = math.sqrt(depth ** 2 + 2 * depth * a)
            distance = a * math.log((scope_0 / a) + math.sqrt((scope_0 / a) ** 2 + 1))
        else:
            distance = 0
        gear_lat, gear_lon = self._functions.get_lat_lon(lat1=record["latitude"], lon1=record["longitude"],
                                                           bearing=bearing, range=distance)
        logging.info(f"starting gear lat/lon: {gear_lat}, {gear_lon}")

        #################################################################################
        # Start Haul > Doors Fully Out Phase
        #
        #   Scope is incrementally increasing from the Start Haul to the Doors Fully Out
        #
        #   Don't start increasing the scope until the depth is greater than 1 meter as well, for
        #   otherwise there can be a lot of values close to the start of haul where the depth is
        #   less than 1 meter, and so no scope has really been let out.
        #
        #################################################################################

        # TODO Todd Hay - Change this to not be hardcoded to 1 meter, but rather once we see it changing at a certain rate

        # Mask when the depth is <= 1 meter
        mask = (df_gear["times"] >= start_haul) & (df_gear["times"] <= doors_fully_out) & (df_gear["depth"] <= 1)
        df_gear.loc[mask, "scope"] = 0
        df_gear.loc[mask, "a"] = 1000000
        df_gear.loc[mask, "range"] = 0

        # Mask when the depth is > 1 meter
        mask = (df_gear["times"] >= start_haul) & (df_gear["times"] <= doors_fully_out) & (df_gear["depth"] > 1)
        num_pts = len(df_gear.loc[mask])
        if num_pts == 1:
            logging.info(f"depth masking greater than 1m returns a single point, which leads to division by zero")
            return
        scope_grow_rate = scope / (num_pts - 1)
        logging.info(f"Number of points before the tow starts: {num_pts}")

        df_gear.loc[mask, "scope"] = [i * scope_grow_rate for i in range(num_pts)]
        df_gear.loc[mask, "a"] = df_gear.loc[mask].apply(lambda x: (x["scope"]**2 - x["depth"]**2) / (2*x["depth"])
                                                         if x["depth"] != 0 and not math.isnan(x["depth"]) else None, axis=1)
        df_gear.loc[mask, "range"] = df_gear.loc[mask] \
            .apply(lambda x: x["a"] * math.log((x["scope"] / x["a"]) + math.sqrt((x["scope"] / x["a"]) ** 2 + 1))
                if not math.isnan(x["a"]) and x["a"] != 0 else None, axis=1)

        #################################################################################
        # Doors Fully Out > Start Haulback Phase
        #
        #   Scope is static during this phase.  The fishing operation occurs during this time, beginning
        #           at the Doors Fully Out waypoint and concluding at the Start Haulback waypoint
        #
        #################################################################################
        mask = (df_gear["times"] >= doors_fully_out) & (df_gear["times"] < start_haulback)
        df_gear.loc[mask, "scope"] = scope
        df_gear.loc[mask, "a"] = df_gear.loc[mask].apply(lambda x: (x["scope"]**2 - x["depth"]**2) / (2*x["depth"])
                                                            if x["depth"] != 0 and not math.isnan(x["depth"]) else None, axis=1)
        df_gear.loc[mask, "range"] = df_gear.loc[mask]\
                .apply(lambda x: x["a"] * math.log((x["scope"]/x["a"]) + math.sqrt((x["scope"]/x["a"])**2 + 1))
                                    if not math.isnan(x["a"]) and x["a"] != 0 else None, axis=1)

        #################################################################################
        # Start Haulback > End of Haul Phase
        #
        #   Scope is incrementally decreasing from Start Haulback to End of Haul
        #
        #################################################################################
        mask = (df_gear["times"] >= start_haulback) & (df_gear["times"] <= end_of_haul)
        post_haulback_size = len(df_gear.loc[mask])

        # path = os.path.expanduser("~/Desktop/df_cat.csv")
        # df_gear.loc[:, ['times', 'latitude', 'longitude', 'a', 'scope', 'depth', 'range', 'track made good', 'bearing', 'gear_lat', 'gear_lon']].to_csv(path)

        # Decrement Scope, then calculate a, approach
        scope_shrink_rate = scope / (post_haulback_size-1)
        df_gear.loc[mask, "scope"] = [scope - i * scope_shrink_rate for i in range(post_haulback_size)]
        df_gear.loc[mask, "a"] = df_gear.loc[mask].apply(lambda x: (x["scope"]**2 - x["depth"]**2) / (2*x["depth"])
                                                     if x["depth"] != 0 and not math.isnan(x["depth"]) else None, axis=1)
        df_gear.loc[mask, "range"] = df_gear.loc[mask]\
                .apply(lambda x: x["a"] * math.log((x["scope"]/x["a"]) + math.sqrt((x["scope"]/x["a"])**2 + 1))
                                    if not math.isnan(x["a"]) and x["a"] != 0 else None, axis=1)

        #################################################################################
        # Calculate all of the gear lat/lon values using the C DLL function
        #################################################################################
        start = arrow.now()

        mask = (df_gear["times"] >= start_haul) & (df_gear["times"] <= end_of_haul)
        num_rows = len(df_gear.loc[mask])

        # Prepare the vessel_data structure for passing into the C DLL
        vessel_data = df_gear.loc[mask, ["latitude", "longitude", "range"]].copy(deep=True).as_matrix()
        vessel_data = np.ascontiguousarray(vessel_data, dtype=np.double)
        vessel_ctypes = [np.ctypeslib.as_ctypes(array) for array in vessel_data]
        vessel_ptr = (POINTER(c_double) * num_rows)(*vessel_ctypes)

        # Prepare gear_data data structure to catch gear lat/lon values calculated via C DLL function
        gear_data = np.zeros([num_rows, 3], dtype=np.double)
        gear_ctypes = [np.ctypeslib.as_ctypes(array) for array in gear_data]
        gear_ptr = (POINTER(c_double) * num_rows)(*gear_ctypes)

        # Calculate gear lat/lon values from the C DLL
        geodll.get_gear_lat_lon(c_int(num_rows), vessel_ptr, c_double(gear_lat), c_double(gear_lon), gear_ptr)

        end = arrow.now()
        logging.info(f"C DLL Iterations:  {num_rows} iterations took {(end-start).total_seconds():.4f}s")

        # Add the gear_data back to the pandas data frame:
        df_gear.loc[mask, "gear_lat"] = [gear_data[i][0] for i in range(num_rows)]
        df_gear.loc[mask, "gear_lon"] = [gear_data[i][1] for i in range(num_rows)]
        df_gear.loc[mask, "bearing"] = [gear_data[i][2] for i in range(num_rows)]

        path = os.path.expanduser("~/Desktop/df_gear_cat.csv")
        # df_gear.loc[:, ['times', 'latitude', 'longitude', 'a', 'scope', 'depth', 'range', 'track made good', 'bearing', 'gear_lat', 'gear_lon']].to_csv(path)

        return df_gear

    def create_gearline_by_smoothed_line(self, df_trackline, span):
        """
        Method to create a gear line from the ITI time series data for the given technique.  These techniques will
        include iti r/b or iti $iigll.
        :param df_trackline: pandas DataFrame
        :param span: int - size of the running mean window
        :return:
        """
        df_gear = df_trackline.copy(deep=True)
        df_gear.drop_duplicates(subset=['times'], keep="first", inplace=True)  # Required, headings are at 4 Hz
        df_gear.loc[:, ["latitude", "longitude"]] = \
            df_gear.loc[:, ["latitude", "longitude"]].rolling(window=span, center=True).mean()
        df_gear = df_gear.rename(columns={"latitude": "gear_lat", "longitude": "gear_lon"})

        return df_gear




    # Utilities only - NOT SURE THAT I'M EVEN USING THESE ANYMORE EITHER
    def calculate_vessel_gcd(self, df_vessel, begin_tow, start_haulback):
        """
        Method to calculate the Great Circle Distance of the vessel from begin tow to start haulback
        :param df_vessel:
        :param begin_tow:
        :param start_haulback:
        :return:
        """
        mask = (df_vessel["times"] >= begin_tow) & (df_vessel["times"] < start_haulback)
        df_gcd = df_vessel.loc[mask].copy(deep=True)
        distance_M = self._functions.get_distance(lat1=df_gcd.iloc[0].loc["latitude"],
                                                lon1=df_gcd.iloc[0].loc["longitude"],
                                                lat2=df_gcd.iloc[-1].loc["latitude"],
                                                lon2=df_gcd.iloc[-1].loc["longitude"])
        distance_N = distance_M * N_PER_M
        speed = distance_N / ((arrow.get(start_haulback) - arrow.get(begin_tow)).total_seconds() / 3600)

        return distance_N, speed


    def calculate_catenary_missing_scope(self, depth, range, initial):
        """
        Calculate the catenary a (shape factor) when we have the depth and range, but no scope
        :param depth: vertical distance from the lowest point of the tow line to the vessel
        :param range: horizontal distance between the supports
        :param initial:
        :return:
        """

        # :param h2: vertical distance between the higher and lower support points, always 0 for us
        h2 = 0

        def f(a):
            return range - a * (np.arccosh((depth + a) / a) + np.arccosh((depth - h2 + a) / a))

        solution = self._functions.newton(f, initial)
        return solution

    def calculate_catenary_missing_range(self, depth, scope, initial):
        """
        Calculate catenary a (shape factor) when we have the depth and the scope.
        :param depth: vertical distance from the lowest point of the tow line to the vessel
        :param L: scope of the tow line (i.e. how much let out)
        :param initial:
        :return:
        """

        # :param h2: vertical distance between the higher and lower support points, always 0 for us
        h2 = depth
        h2 = 0

        def f(a):
            return scope - a * (np.sinh(np.arccosh((depth + a) / a)) + np.sinh(np.arccosh((depth - h2 + a) / a)))

        solution = self._functions.newton(f, initial)
        return solution


    # NOT USED I DON'T THINK
    def create_prehaulback_gearline_by_range_extrapolation(self, df_vessel, doors_fully_out, begin_tow, start_haulback, scope, padding, span):
        """
        Method to calculate the df_pre by the range extrapolation method.  This uses the provided scope
        and the instantaneous depth values to calculate the range, and then assuming a bearing of 180 degrees
        (straight behind) the vessel, calculates the gear position using the vessel lat / lon and the gear range / bearing
        :param df_vessel: pandas DataFrame - contains the vessel track
        :param begin_tow: arrow Date/Time - when the tow started
        :param start_haulback: arrow Date/Time - when the haulback was started
        :param span: int -
        :return:
        """
        # Mask and pad the df_vessel track.  Padding use to buffer the running mean calculation only
        mask = (df_vessel["times"] >= doors_fully_out) & (df_vessel["times"] < start_haulback)
        df_pre = df_vessel.loc[mask]
        start = df_vessel.index.get_loc(df_pre.head(1).index.tolist()[0]) #- padding  #- 1  # Subtract an extra for waypoint transfer later on
        end = df_vessel.index.get_loc(df_pre.tail(1).index.tolist()[0]) + padding   #+ 1
        df_pre = df_vessel.iloc[start:end].copy(deep=True)

        # Calculate the Pre-Haulback Range
        df_pre.loc[:, "range"] = df_pre.apply(lambda x: math.sqrt(scope ** 2 - x["depth"] ** 2) if scope > x["depth"] else None, axis=1)

        # Calculate the gear_lat and gear_lon
        df_pre["gear_lat"] = df_pre.apply(lambda x: self._functions.get_lat(lat=x["latitude"],
                                                                            lon=x["longitude"],
                                                                            bearing=x["bearing"],
                                                                            range=x["range"]), axis=1)
        df_pre["gear_lon"] = df_pre.apply(lambda x: self._functions.get_lon(lat=x["latitude"],
                                                                            lon=x["longitude"],
                                                                            bearing=x["bearing"],
                                                                            range=x["range"]), axis=1)

        # Smooth the df_pre line with a running mean
        df_pre.loc[:, ["gear_lat", "gear_lon"]] = df_pre.loc[:, ["gear_lat", "gear_lon"]].rolling(window=span,
                                                                                                  center=True).mean()

        return df_pre

    def calculate_catenary(self, depth, range, initial):
        """
        Calculate catenary a (openness) value when provided the depth and range, but no scope
        :param depth:
        :param range:
        :param initial:
        :return:
        """
        def f(a):
            return (depth + a) / a - np.cosh(range / (2 * a))

        solution = self._functions.newton(f, initial)
        return solution

    def create_gearline_by_catenary(self, df_vessel, bearing_type, doors_fully_out, begin_tow, start_haulback,
                                    net_off_bottom, doors_at_surface, padding, scope, span):
        """
        This method creates a gear trackline using a pure catenary method.  The basic method is as follows:

        Range Calculation - done using catenary with the current depth
        Bearing Calculation - calculate the bearing via one of two methods:
            a. Get vessel start/end points, and calculate an overall bearing to be used by the catenary
            b. Get vessel bearing and create a running mean to smooth it out and use this for the catenary
        :param df_vessel:
        :param scope:
        :param span:
        :return:
        """
        # Get the df_gear
        mask = (df_vessel["times"] >= doors_fully_out) & (df_vessel["times"] <= doors_at_surface)
        df_gear = df_vessel.loc[mask]

        # Bearing Method A. Vessel start/end points to calculate overall bearing
        if bearing_type == "vessel_gcd":

            mask = (df_vessel["times"] >= begin_tow) & (df_vessel["times"] <= net_off_bottom)
            df_masked_vessel = df_vessel.loc[mask]
            vessel_start = df_masked_vessel.head(1).iloc[0]
            vessel_end = df_masked_vessel.tail(1).iloc[0]

            distance, bearing = self._functions.get_distance_bearing(lat1=vessel_start["latitude"], lon1=vessel_start["longitude"],
                                                                  lat2=vessel_end["latitude"], lon2=vessel_end["longitude"])
            df_gear.loc[:, "bearing"] = bearing - 180 if bearing-180 >= 0 else bearing + 180

        # Bearing Method B. Smoothed vessel bearing
        elif bearing_type == "vessel_smoothed":
            df_gear["bearing"] = df_gear.apply(lambda x: (x["track made good"] - 180)   # Calculate the net bearing from vessel heading
                            if (x["track made good"] - 180) >= 0 else x["track made good"] + 180, axis=1)    # Create Bearing
            df_gear.loc[:, "bearing"] = df_gear.loc[:, "bearing"].rolling(window=span).mean()

        # Bearing Method C. Point-wise bearing, no smoothingn
        elif bearing_type == "standard":
            df_gear["bearing"] = df_gear.apply(lambda x: (x["track made good"] - 180)   # Calculate the net bearing from vessel heading
                            if (x["track made good"] - 180) >= 0 else x["track made good"] + 180, axis=1)    # Create Bearing

        # Bearing Method D. Large Smoothing from Vessel Position to Gear Position.  Take a span of the number of points
        # between where the vessel is at begin_tow and trace backwards by the initial scope size, achieved by going back
        # the number of vessel track points whose segment distance sum equals the size of the initial scope
        elif bearing_type == "vessel_scope_mean":

            df_vessel_dist = df_vessel.copy(deep=True)
            # df_vessel_dist.loc[:, ["latitude", "longitude"]] = df_vessel_dist.loc[:, ["latitude", "longitude"]]\
            #     .rolling(window=span).mean()
            df_vessel_dist["latitude2"] = df_vessel_dist["latitude"].shift()
            df_vessel_dist["longitude2"] = df_vessel_dist["longitude"].shift()
            df_vessel_dist["dist"] = df_vessel_dist.apply(lambda x: self._functions.get_distance(x["latitude"], x["longitude"],
                                                                                   x["latitude2"], x["longitude2"]), axis=1)
            mask = (df_vessel_dist["times"] <= begin_tow)
            df_vessel_dist = df_vessel_dist.loc[mask]
            df_vessel_dist["sum"] = df_vessel_dist.iloc[::-1].loc[:, "dist"].cumsum()[::-1]
            mask = (df_vessel_dist["sum"] <= scope)
            df_vessel_dist = df_vessel_dist.loc[mask]

            vessel_scope_span = len(df_vessel_dist)
            logging.info(f"begin_tow: {begin_tow}, scope: {scope}")
            logging.info(f"number of points to include: {vessel_scope_span}")

            df_vessel.loc[:, "smoothed heading"] = df_vessel.loc[:, "track made good"].rolling(window=vessel_scope_span).mean()
            df_gear = df_gear.assign(smoothed_heading=df_vessel["smoothed heading"])
            df_gear["bearing"] = df_gear.apply(lambda x: (x["smoothed_heading"] - 180)
                                                 if x["smoothed_heading"] - 180 >= 0 else x["smoothed_heading"]+180, axis=1)

        # Begin the catenary calculation.  Find the shape factor, a, of the catenary at begin_tow with the
        # starting depth and starting scope
        mask = (df_gear["times"] == begin_tow)
        depth = df_gear.loc[mask].iloc[0]["depth"]

        # initial_guess = 100
        # a = self.calculate_catenary_missing_range(depth=depth, scope=scope, initial=initial_guess)
        # distance = a * np.arccosh((depth+a) / a)
        # logging.info(f"OLD:  depth: {depth}, scope: {scope}, a: {a}, distance: {distance}")

        a = (scope**2 - depth**2)/(2*depth)
        scope_0 = math.sqrt(depth**2 + 2*depth*a)
        distance = a * math.log((scope_0 / a) + math.sqrt((scope_0/a)**2 + 1))



        # Now start moving the net along the bottom, but the range will stay constant as the scope isn't changing
        # Do this until start_haulback happens
        df_gear.loc[df_gear["times"] < start_haulback, "range"] = distance

        # At start_haulback, start pulling in the scope, and thus calculate the new range from it.  This requires
        # tightening up the shape factor, a, until we hit the net off bottom point
        post_haulback_size = len(df_gear.loc[df_gear["times"] >= start_haulback])

        # df_gear.loc[df_gear["times"] >= start_haulback, "scope"] = [scope - i for i in range(post_haulback_size)]
        # df_gear.loc[df_gear["times"] >= start_haulback, "a"] = df_gear.loc[df_gear["times"] >= start_haulback] \
        #     .apply(lambda x: (x["scope"]**2 - x["depth"]**2) / (2*x["depth"]), axis=1)

        df_gear.loc[df_gear["times"] >= start_haulback, "a"] = [a - i*2 for i in range(post_haulback_size)]


        df_gear.loc[df_gear["times"] >= start_haulback, "scope"] = \
            df_gear.loc[df_gear["times"] >= start_haulback] \
                .apply(lambda x: math.sqrt(x["depth"]**2 + 2*x["depth"]*x["a"]) if x["a"] > 0 else None, axis=1)

        df_gear.loc[df_gear["times"] >= start_haulback, "range"] = \
            df_gear.loc[df_gear["times"] >= start_haulback]\
                .apply(lambda x: x["a"] * math.log((x["scope"]/x["a"]) + math.sqrt((x["scope"]/x["a"])**2 + 1))
                                    if not math.isnan(x["a"]) else None, axis=1)

        # df_gear.loc[df_gear["times"] >= start_haulback, "range"] = \
        #     df_gear.loc[df_gear["times"] >= start_haulback]\
        #         .apply(lambda x: x["a"] * np.arccosh((x["depth"] + x["a"]) / x["a"]) if a > 0 else 0, axis=1)

        logging.info(f"df_gear: {df_gear.loc[:,['times', 'depth', 'a', 'scope', 'range']]}")


        # Determine where the vessel speed starts decreasing and then levels out
        # df_post["speed_mean"] = df_post["speed over ground"].rolling(window=span, center=True).mean()
        # df_post["speed_change"] = df_post["speed_mean"].pct_change()
        # df_post.loc[:, "range"] = None
        # mask = (df_post["speed_change"].abs() >= SPEED_CHANGE_PCT)
        # df_change = df_post.loc[mask]



        # Calculate the gear_lat and gear_lon with the newly generated bearing and range information
        df_gear["gear_lat"] = df_gear.apply(lambda x: self._functions.get_lat(lat=x["latitude"],
                                                                              lon=x["longitude"],
                                                                              bearing=x["bearing"],
                                                                              range=x["range"]), axis=1)
        df_gear["gear_lon"] = df_gear.apply(lambda x: self._functions.get_lon(lat=x["latitude"],
                                                                              lon=x["longitude"],
                                                                              bearing=x["bearing"],
                                                                              range=x["range"]), axis=1)

        # Smooth the df_post line using a running mean
        df_gear.loc[:, ["gear_lat", "gear_lon"]] = df_gear.loc[:, ["gear_lat", "gear_lon"]].rolling(window=span,
                                                                                                    center=True).mean()

        # path = os.path.expanduser("~/Desktop/df_catenary.csv")
        # df_gear.loc[:, ['times', 'depth', 'scope', 'a', 'range', 'speed over ground', 'track made good', 'smoothed_heading', 'bearing', 'gear_lat', 'gear_lon']].to_csv(path)

        # path = r"C:\Users\Todd.Hay\Desktop\depth.csv"
        # df_vessel.loc[:, ['times', 'latitude', 'longitude', 'scope', 'depth', 'range', 'track made good', 'bearing']].to_csv(path)


        logging.info(f"BT: {begin_tow}, SH: {start_haulback}, NOB: {net_off_bottom}")
        # logging.info(f"{df_gear.loc[1618:1699, ['times', 'depth', 'range', 'a', 'gear_lat', 'gear_lon']]}")

        return df_gear

    def create_posthaulback_gearline_by_catenary(self, depth, range, df_trig, df_post, scope, span, padding):
        """
        Method to calculate the posthaulback gearline using a combination of the catengary equation and the trig method

        In this scenario, there are twp\o segments of the post haulback gear line to include:

        --------------------------------------------------------------------------------------------------------
        | Segment       | Description               |   Start           | End           |

        - Slack To Taut - it is assumed that there is some slack in the tow line that must first be pulled taut for the
                            net to then start moving
        - Taut

        :param depth: depth at the end of Pre Haulback - df_pre
        :param range: range at the end of Pre Haulback - df_pre
        :param df_trig:
        :param df_post:
        :param scope:
        :param span:
        :return:
        """
        if df_trig is None or df_post is None:
            return

        # Gather static values for the trig method
        time_diff = (df_trig["times"].iloc[-1] - df_trig["times"].iloc[0+padding]).seconds  # Start Haulback to Doors At Surface
        ratio = scope / time_diff                                                   # Ratio of Scope to Time Diff
        trig_end_time = df_trig["times"].iloc[-1]                                   # Time at Doors At Surface

        # Calculate and assign the scope
        df_trig.loc[:, "scope"] = df_trig.apply(lambda x: (trig_end_time - x["times"]).seconds * ratio, axis=1)
        df_post = df_post.assign(trig_scope=df_trig["scope"])

        # Determine where the vessel speed starts decreasing and then levels out
        # df_speed = df_post.copy(deep=True)
        df_post["speed_mean"] = df_post["speed over ground"].rolling(window=span, center=True).mean()
        df_post["speed_change"] = df_post["speed_mean"].pct_change()
        df_post.loc[:, "range"] = None

        # logging.info(f"speed change: {df_post.loc[:,['times', 'speed over ground', 'speed_mean', 'speed_change']]}")
        mask = (df_post["speed_change"].abs() >= SPEED_CHANGE_PCT)
        df_change = df_post.loc[mask]
        if df_change.empty:
            return None

        start = df_post.index.get_loc(df_change.head(1).index.tolist()[0])
        end = df_post.index.get_loc(df_change.tail(1).index.tolist()[0])
        df_slack = df_post.iloc[start:end].copy(deep=True)

        # Calculate thhe range using the catenary method
        initial_guess = 100
        a = self.calculate_catenary(depth=depth, range=range, initial=initial_guess)
        df_post.loc[:, "range"] = df_post.apply(lambda x: a * math.acosh((x["depth"] + a) / a), axis=1)

        df_slack.loc[:, "range"] = df_slack.apply(lambda x: a * math.acosh((x["depth"] + a) / a), axis=1)

        # Calculate the range from the scope + depth using pythagorean theorem, i.e  Trig Method
        df_taut = df_post.iloc[end+1:].copy(deep=True)
        df_taut.loc[:, "range"] = \
            df_taut.apply(lambda x: math.sqrt(x["trig_scope"] ** 2 - x["depth"] ** 2) if x["trig_scope"] > x["depth"] else None, axis=1)
        df_slack = df_slack.append(df_taut)

        # Calculate the gear_lat and gear_lon
        df_post["gear_lat"] = df_post.apply(lambda x: self._functions.get_lat(lat=x["latitude"],
                                                                              lon=x["longitude"],
                                                                              bearing=x["bearing"],
                                                                              range=x["range"]), axis=1)
        df_post["gear_lon"] = df_post.apply(lambda x: self._functions.get_lon(lat=x["latitude"],
                                                                              lon=x["longitude"],
                                                                              bearing=x["bearing"],
                                                                              range=x["range"]), axis=1)

        # Smooth the df_post line using a running mean
        df_post.loc[:, ["gear_lat", "gear_lon"]] = df_post.loc[:, ["gear_lat", "gear_lon"]].rolling(window=span,
                                                                                                    center=True).mean()

        # logging.info(f"df_post: {df_post.loc[:, ['times', 'scope', 'depth', 'range']]}")
        # logging.info(f"First + Last rows of df_post:\n{pd.concat([df_post['times'].head(3), df_post['times'].tail(3)])}")

        return df_post
