import QtQuick 2.5
import QtQuick.Controls 1.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Window 2.0

import "."
import "../common"

Dialog {
    id: dlg
    width: 800
    height: 500
    title: "GPS Entry"

    property alias enable_audio: numPad.enable_audio

    // Capture datetime, lat/long, and depth.
    // Lat/long is restricted to positive latitude and negative longitude
    // (Northwestern quadrasphere containing U.S coastal locations).
    // I.e. Values are restricted to positive lat and negative long
    // (no +/- signs need be entered).

    // Field validation convention: if a validation fails, clear the offending field.
    // Emptying the field will disable the Done button.

    // Cursor positioning convention: if re-entering a text field connected to a num keypad,
    // and that field already contains digits, position the cursor after the last digit.
    // Rationale: entry could be occurring on backdeck without a stylus and using a gloved finger;
    // a backspace button is available and the fields are short (2-4 digits).

    // Maximum trawling depth and minimum/maximum latitude locations
    // are specified in the SETTINGS table of Observer.db
    property int trawl_max_depth_fathoms: appstate.trawlMaxDepthFathoms
    property int trawl_min_latitude_degrees: appstate.trawlMinLatitudeDegrees
    property int trawl_max_latitude_degrees: appstate.trawlMaxLatitudeDegrees

    property int default_fontsize_pixels: 25
    property int default_tf_height: 50  // Matching ObserverSettings.default_tf_height
                                        // Issue: OK for control in common to access ..\observer?
    property int expected_lat_degree_digits: 2
    property int expected_long_degree_digits: 3
    property int expected_minutes_digits: 2
    property int expected_minutes_decimal_places: 2
    property int max_minutes_decimal_places: 4
    property int max_depth_decimal_places: 2

    property alias sub_title: entry_title.text

    property var location_id: null  // This is the actual DB location ID
    property int position_number: -1

    property var time_val: null
    property var lat_degs: 0.0
    property var long_degs: 0.0

    // Track currently focused TextField so that connection can be re-established after numpad CLR key.
    property TextField current_textfield: null
    property string current_textfield_name: "None"

    function enable_OK_button_if_required_fields_not_empty() {
        // If time, lat degrees, long degrees, and depth have values, enable the dialog OK button, else disable
        btnOK.state = (tfTime.text.length > 0 &&
                tfLatDeg.text.length > 0 &&
                tfLongDeg.text.length > 0 &&
                tfDepth.text.length > 0) ? "enabled" : "disabled";
                //console.debug("btnOK state is '" + btnOK.state + "' " +
                //"(" + tfTime.text.length + "/" + tfLatDeg.text.length + "/" +
                //tfLongDeg.text.length + "/" + tfDepth.text.length + ")"
                //);
    }

    function update_current_textfield(textfield, textfield_name) {
        var text_from = current_textfield ? current_textfield.text : "(undefined)";
        var text_to = textfield ? textfield.text : "(undefined)";
        //console.debug("Switching from '" + current_textfield_name +
         //       "' with text = '" + text_from + "'" +
         //       " to '" + textfield_name + "' with text = '" + text_to + "'.");
        current_textfield = textfield;
        current_textfield_name = textfield_name;
    }

    function calc_longitude_ddegs() {
        // If no value entered yet into degrees or minutes, set to zero for this calculation.
        var longDeg = (tfLongDeg.text.length == 0) ? 0 : parseInt(tfLongDeg.text);
        var longMinWhole = (tfLongMinWhole.text.length == 0) ? 0 : parseInt(tfLongMinWhole.text);
        // Do not pre-parse fractional minutes, e.g. 0.06 will become 0.6
        var longMinFract = tfLongMinFract.text.trim();
        var longMin = parseFloat(longMinWhole + "." + longMinFract);

        //console.debug("longDeg=" + longDeg + "; longMin=" + longMin + ".");
        // Western hemisphere (negative longitude). Negate the positive value entered.
        var long_degs = -1 * CommonUtil.calc_decimal_degs(longDeg, longMin);
        //console.debug("long_degs=" + long_degs);
        return long_degs;
    }

    function calc_latitude_ddegs() {
        // If no value entered yet into degrees or minutes, set to zero for this calculation.
        var latDeg = (tfLatDeg.text.length == 0) ? 0 : parseInt(tfLatDeg.text);
        var latMinWhole = (tfLatMinWhole.text.length == 0) ? 0 : parseInt(tfLatMinWhole.text);
        // Do not pre-parse fractional minutes, e.g. 0.06 will become 0.6
        var latMinFract = tfLatMinFract.text.trim();
        var latMin = parseFloat(latMinWhole + "." + latMinFract);
        var lat_degs = CommonUtil.calc_decimal_degs(latDeg, latMin);
        //console.debug("calc_lat_degs=" + lat_degs);
        return lat_degs;
    }

    function minute_whole_to_field_string(min_whole, min_fract) {
        // Return text value of min_whole, with one exception:
        // if min_whole is 0 and min_fract is 0 as well, return empty string.
        if (min_whole > 0 || min_fract > 0) {
            return min_whole;
        }
        //console.debug("Both minutes whole and fractional are zero");
        return "";
    }

    function minute_fract_to_field_string(flt_min_fract) {
        // Expected a float value between [0 and 1).
        // Need to put it into a text field, essentially as an integer.
        // - without the decimal place (that's explicitly in a label field)
        // - without trailing zeros.
        flt_min_fract = flt_min_fract.toFixed(2);
        //console.debug("flt_min_fract to " + max_minutes_decimal_places + " places = " + flt_min_fract);
        if (flt_min_fract < 0 || flt_min_fract >= 1)
            console.error("flt_min_fract of " + flt_min_fract + " is not in [0, 1).");

        // Preserve leading zeros
        var str_min_fract = flt_min_fract.toString().substr(2);
        return str_min_fract;
    }

    function set_values_from_decimal_degs() {
        // Initialize this dialog text box values for lat and long.
        // Assumes lat_degs and long_degs are set.
        // N.B. Absolute longitudinal value used here to fill its text box, without sign;
        // code converts to negative before storing to database.

        console.debug(" At entry, lat_degs=" + lat_degs + " and long_degs=" + long_degs);
        if (lat_degs < 0)
            console.error("expected lat to be positive, not " + lat_degs);
        if (long_degs > 0)
            console.error("expected long to be negative, "
                + "not " + long_degs);

        // calc degrees + decimal minutes, set text boxes

        // Set three latitude fields
        var lat_deg_whole = Math.floor(lat_degs);
        // Round minutes to the number of decimal places that will be displayed: 2 for minutes (whole),
        // max_minutes_decimal_places (currently 4) for fraction of minutes.
        var lat_min_dec = ((lat_degs - lat_deg_whole) * 60.0).toFixed(2 + max_minutes_decimal_places);
        var lat_min_whole = Math.floor(lat_min_dec);
        var lat_min_fract = lat_min_dec - lat_min_whole;

        tfLatDeg.text = lat_deg_whole;
        tfLatMinWhole.text = minute_whole_to_field_string(lat_min_whole, lat_min_fract);
        tfLatMinFract.text = minute_fract_to_field_string(lat_min_fract);
        console.debug("latmin_text=" + tfLatMinWhole.text + "." + tfLatMinFract.text);

        // Set three longitude fields. N.B. field value is absolute (positive). Negative sign in label.
        var long_degs_abs = Math.abs(long_degs);
        var long_deg_whole = Math.floor(long_degs_abs);
        //console.debug("long_deg_whole after Math.floor=" + long_deg_whole);
        // Round minutes to the number of decimal places that will be displayed:
        // 2 for minutes (whole),
        // max_minutes_decimal_places (currently 4) for fraction of minutes.
        var long_min_dec = ((long_degs_abs - long_deg_whole) * 60.0).toFixed(2 + max_minutes_decimal_places);
        //console.debug("long_min_dec=" + long_min_dec);
        var long_min_whole = Math.floor(long_min_dec);
        var long_min_fract = long_min_dec - long_min_whole;

        tfLongDeg.text = long_deg_whole;
        tfLongMinWhole.text = minute_whole_to_field_string(long_min_whole, long_min_fract);
        tfLongMinFract.text = minute_fract_to_field_string(long_min_fract);
        console.debug("longmin_text=" + tfLongMinWhole.text + "." + tfLongMinFract.text);
    }

    function degmins_to_string(degrees_text, minutes_whole_text, minutes_fract_text) {
        // Explicitly type to string to allow use of length property
        degrees_text = String(degrees_text);
        minutes_whole_text = String(minutes_whole_text);
        minutes_fract_text = String(minutes_fract_text);

        var degmins_text = (degrees_text.length == 0)? "0": degrees_text;
        degmins_text += "° ";

        minutes_whole_text = (minutes_whole_text.length == 0) ? "0" : minutes_whole_text;
        minutes_fract_text = (minutes_fract_text.length == 0) ? "0" : minutes_fract_text;

        if (minutes_whole_text != "0" || minutes_fract_text != "0") {
            degmins_text += minutes_whole_text + "." + minutes_fract_text + "' ";
        }
        return degmins_text;
    }

    ////
    // Validation Utilities
    ////

    // From Section "A Stricter Parse Function" here:
    // (https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/parseInt)
    // Difference from JavaScript parseInt: if float value, return NaN rather than integer portion.
    // Do treat all zeros in decimal places as integer.
    function strict_parse_int(numeric_text) {
        if(/^(\-|\+)?([0-9]+)(\.0*)?$/.test(numeric_text))
            return Number(numeric_text);
        return NaN;
    }

    function round_numeric_txt_to_max_decimals(numeric_text, max_decimals) {
        if (numeric_text.length == 0)
            return numeric_text;

        // If integer value, don't clutter with zeroes in decimal places.
        var text_as_integer = strict_parse_int(numeric_text);
        if (!isNaN(text_as_integer))
            return String(text_as_integer);

        // Round float to maximum decimal places:
        var text_as_float = parseFloat(numeric_text).toFixed(max_decimals);

        // Strip any trailing zeros.
        var float_as_text = String(text_as_float);
        while (float_as_text.slice(-1) == "0") {
            float_as_text = float_as_text.slice(0, float_as_text.length - 1);
        }
        return float_as_text;
    }

    function minutes_are_not_empty(component_to_check) {
        if (component_to_check == "Latitude") {
            return tfLatMinWhole.text.length > 0 || tfLatMinFract.text.length > 0;
        } else if (component_to_check == "Longitude") {
            return tfLongMinWhole.text.length > 0 || tfLongMinFract.text.length > 0;
        } else {
            console.error("unrecognized component " + component_to_check);
        }
    }
    function clear_minutes(component_to_clear) {
        if (component_to_clear == "Latitude") {
            tfLatMinWhole.text = "";
            tfLatMinFract.text = "";
        } else if (component_to_clear == "Longitude") {
            tfLongMinWhole.text = "";
            tfLongMinFract.text = "";
        } else {
            console.error("unrecognized component " + component_to_clear);
        }
    }
    function clear_degrees_and_minutes(component_to_clear) {
        if (component_to_clear == "Latitude") {
            tfLatDeg.text = "";
        } else if (component_to_clear == "Longitude") {
            tfLongDeg.text = "";
        } else {
            console.error("unrecognized component " + component_to_clear);
        }
        clear_minutes(component_to_clear);
    }

    function validation_error_window_is_visible() {
        return dlgMinutesTooLarge.visible
            || dlgLatOrLongOutOfRange.visible
            || dlgDepthTooGreat.visible;
    }

    ////
    // Single-Field Validations
    ////

    function validate_degrees(component_to_check, degrees_text_to_check) {
        // Check that degrees text field, by itself (no minutes), is within range.
        // component_to_check: "Latitude" || "Longitude"
        // degrees_text_to_check: typically tfLatDeg.text || tfLongDeg.text.
        // Return value: -1 (val not performed); 0 (val failed); 1 (val passed).

        // If validation-failed dialog already displayed, done.
        // Covers corner-case that should not happen: edit existing location with multiple errors.
        if (validation_error_window_is_visible()) {
            console.warn("validate_minutes: validation error window already showing. "
                + "Val on " + component_to_check + "'s minutes not performed");
            return -1;
        }

        degrees_text_to_check = String(degrees_text_to_check);
        // Don't perform validation on empty field
        if (degrees_text_to_check.length == 0)
            return -1;

        var degrees_to_check = parseInt(degrees_text_to_check);
        var degmins_str = degmins_to_string(degrees_text_to_check, "", "");
        if (component_to_check == "Latitude") {
            if (degrees_to_check < trawl_min_latitude_degrees) {
                dlgLatOrLongOutOfRange.component_offended = "Latitude";
                dlgLatOrLongOutOfRange.offending_value = degmins_str;
                dlgLatOrLongOutOfRange.polarity_offended = "less";
                dlgLatOrLongOutOfRange.bound_offended = String(trawl_min_latitude_degrees);
                console.warn("Displaying dialog: Latitude entered is less than",
                        trawl_min_latitude_degrees, "degrees.");
                dlgLatOrLongOutOfRange.open();
                return 0;
            }

            if (degrees_to_check > trawl_max_latitude_degrees) {
                dlgLatOrLongOutOfRange.component_offended = "Latitude";
                dlgLatOrLongOutOfRange.offending_value = degmins_str;
                dlgLatOrLongOutOfRange.polarity_offended = "greater";
                dlgLatOrLongOutOfRange.bound_offended = String(trawl_max_latitude_degrees);
                console.warn("Displaying dialog: Latitude entered is greater than",
                        trawl_max_latitude_degrees, "degrees.");
                dlgLatOrLongOutOfRange.open();
                return 0;
            }
            return 1;
        } else if (component_to_check == "Longitude") {
            // Value is from textbox, which has no sign. Negate and then validate.
            degrees_to_check = -degrees_to_check;
            degmins_str = "-" + degmins_str;
            if (degrees_to_check < -180) {
                dlgLatOrLongOutOfRange.component_offended = "Longitude";
                dlgLatOrLongOutOfRange.offending_value = degmins_str;
                dlgLatOrLongOutOfRange.polarity_offended = "less";
                dlgLatOrLongOutOfRange.bound_offended = "-180";
                console.warn("Displaying dialog: Longitude entered is less than -180 degrees.");
                dlgLatOrLongOutOfRange.open();
                return 0;
            }

            if (degrees_to_check > 0) {
                // Impossible to specify using numpad w/o +/- sign. But catch for devs w/keybd.
                dlgLatOrLongOutOfRange.component_offended = "Longitude";
                dlgLatOrLongOutOfRange.offending_value = degmins_str;
                    //(tfLongMin.text.length == 0)? "0" : tfLongMin.text;
                dlgLatOrLongOutOfRange.polarity_offended = "greater";
                dlgLatOrLongOutOfRange.bound_offended = "0";
                console.warn("Displaying dialog: Longitude " + degmins_str
                    + " is greater than 0 degrees.");
                dlgLatOrLongOutOfRange.open();
                return 0;
            }
            return 1; // Valid degrees.
        } else {
            log.error("Unrecognized component (neither Latitude nor Longitude: "
                + component_to_check);
            return -1;
        }
    }

    function combine_whole_and_fract_minutes(minutes_whole_text, minutes_fract_text) {
        // Return float value of minutes <whole>.<fract>.
        // Assumes that whole is integer value.
        // If fractional portion empty, use zero.
        if (minutes_fract_text.length == 0) {
            minutes_fract_text = "0";
        }
        minutes = parseFloat(minutes_whole_text + "." + minutes_fract_text);
        console.debug("combined minutes = " + minutes);
        return minutes;
    }

    function validate_whole_minutes(component_to_check, minutes_whole_text_to_check) {
        // Check that minutes parameter is within range.
        // component_to_check: "Latitude" || "Longitude"
        // minutes_whole_text_to_check: typically tfLatMinWhole.text || tfLongMinWhole.text.
        // Empty whole minutes: assume zero.
        // Return value: -1 (val not performed); 0 (val failed); 1 (val passed).

        // If validation-failed dialog already displayed, done.
        // Covers corner-case that should not happen: edit existing location with multiple errors.
        if (validation_error_window_is_visible()) {
            console.warn("validate_minutes: validation error window already showing. "
                + "Val on " + component_to_check + "'s minutes not performed");
            return -1;
        }

        // If whole minutes field is empty, set to zero.
        minutes_whole_text_to_check = String(minutes_whole_text_to_check);
        if (minutes_whole_text_to_check.length == 0) {
            minutes_whole_text_to_check = "0"
        }

        // Single-field edit: whole minutes must be less than 60.
        // Return 0 (false) if check failed, 1 (true) if all passed.
        // Do not clear offending field; leave that to caller.
        var minText = (minutes_whole_text_to_check.length == 0)? "0" : minutes_whole_text_to_check;
        var min = parseInt(minText);
        if (min >= 60) {
            console.warn("Displaying dialog: " + component_to_check + " minutes are too large.");
            dlgMinutesTooLarge.component_offended = component_to_check;
            dlgMinutesTooLarge.offending_minutes = min;
            dlgMinutesTooLarge.open();
            return 0;
        }
        return 1; // Valid whole minutes!
    }

    function validate_depth() {
        // If validation-failed dialog already displayed, done.
        // Covers corner-case that should not happen, edit existing location with multiple errors.
        if (validation_error_window_is_visible()) {
            console.warn("validate_depth: validation error window already showing. "
                + "No further val done");
            return -1;
        }

        // Don't validate empty field
        if (tfDepth.text.length == 0)
            return -1;

        if (parseInt(tfDepth.text) > trawl_max_depth_fathoms) {
            console.warn("Displaying dialog: Depth too great.");
            dlgDepthTooGreat.invalidDepth = tfDepth.text
            dlgDepthTooGreat.open()
            tfDepth.text = ""
            return 0;
        }
        return 1;
    }

    ////
    // Two-field validations: minutes and degrees for latitude and for longitude.
    // (Covers the border case where each field is valid, but not together
    //  e.g. Longitude -180 Deg 1 Min).
    //
    // TODO: Simplify/combine validate_lat and validate_long. A lot of code for a corner case.
    ////

    function validate_lat(lat_degs_to_check) {
        // Validate integer latitude, taking both degrees and minutes into account.
        // Display pop-up if out-of-bounds.
        // Supported quadrasphere: NW (Latitude must be positive).

        // Return value: -1 (val not performed); 0 (val failed); 1 (val passed).

        // If a clear of the dialog's fields is in progress, done.
        if (clearInProgress) {
            //console.warn("validate_lat: validation skipped - clear in progress; " +
            //    + "no further val done");
            return -1;
        }
        // If validation-failed dialog already displayed, done.
        // Covers corner-case that should not happen, editing an existing location with multiple errors.
        if (validation_error_window_is_visible()) {
            console.warn("validate_lat: validation error window already showing. "
                + "No further val done");
            return -1;
        }

        //console.debug("Validating lat deg/min.");
        if (lat_degs_to_check < trawl_min_latitude_degrees) {
            dlgLatOrLongOutOfRange.component_offended = "Latitude";
            dlgLatOrLongOutOfRange.offending_value = degmins_to_string(
                tfLatDeg.text, tfLatMinWhole.text, tfLatMinFract.text);
            dlgLatOrLongOutOfRange.polarity_offended = "less";
            dlgLatOrLongOutOfRange.bound_offended = String(trawl_min_latitude_degrees);
            console.warn("Displaying dialog: Latitude entered is less than",
                    trawl_min_latitude_degrees, "degrees.");
            dlgLatOrLongOutOfRange.open();
            clear_degrees_and_minutes("Latitude");
            return 0;
        }

        if (lat_degs_to_check > trawl_max_latitude_degrees) {
            dlgLatOrLongOutOfRange.component_offended = "Latitude";
            dlgLatOrLongOutOfRange.offending_value = degmins_to_string(
                tfLatDeg.text, tfLatMinWhole.text, tfLatMinFract.text);
            dlgLatOrLongOutOfRange.polarity_offended = "greater";
            dlgLatOrLongOutOfRange.bound_offended = String(trawl_max_latitude_degrees);
            console.warn("Displaying dialog: Latitude entered is greater than",
                    trawl_max_latitude_degrees, "degrees.");
            dlgLatOrLongOutOfRange.open();
            clear_degrees_and_minutes("Latitude");
            return 0;
        }
        return 1; // All validation checks passed.
    }

    function validate_long(long_degs_to_check) {
        // Validate float longitude long_degs_to_check.
        // Display pop-up if out-of-bounds.
        // Supported quadrasphere: NW (Longitude negative)

        // Return value: -1 (val not performed); 0 (val failed); 1 (val passed).

        // If validation-failed dialog already displayed, done.
        // Covers corner-case that should not happen, editing an existing location with multiple errors.
        if (validation_error_window_is_visible()) {

            console.warn("validate_long: validation error window already showing. "
                + "No further val done");
            return -1;
        }

       if (long_degs_to_check < -180) {
            dlgLatOrLongOutOfRange.component_offended = "Longitude";
            dlgLatOrLongOutOfRange.offending_value = "-"
                + degmins_to_string(tfLongDeg.text, tfLongMinWhole.text, tfLongMinFract.text);
            dlgLatOrLongOutOfRange.polarity_offended = "less";
            dlgLatOrLongOutOfRange.bound_offended = "-180";
            console.warn("Displaying dialog: Longitude entered is less than -180 degrees.");
            clear_degrees_and_minutes("Longitude");
            dlgLatOrLongOutOfRange.open();
            return 0;
        }

       if (long_degs_to_check > 0) {
            // Will be impossible to specify using numpad w/o +/- sign. But catch for devs w/keybd.
            dlgLatOrLongOutOfRange.component_offended = "Longitude";
            dlgLatOrLongOutOfRange.offending_value = "-"
                + degmins_to_string(tfLongDeg.text, tfLongMinWhole.text, tfLongMinFract.text);
            dlgLatOrLongOutOfRange.polarity_offended = "greater";
            dlgLatOrLongOutOfRange.bound_offended = "0";
            console.warn("Displaying dialog: Longitude " + long_degs + " is greater than 0 degrees.");
            clear_degrees_and_minutes("Longitude");
            dlgLatOrLongOutOfRange.open();
            return 0;
        }
        return 1; // All validation checks passed.
    }

    property alias depth: tfDepth.text

    property bool clearInProgress: false
    function clear() {
        clearInProgress = true;
        sub_title = "";
        time_val = null;
        lat_degs = null;
        long_degs = null;
        clear_degrees_and_minutes("Latitude");
        clear_degrees_and_minutes("Longitude");
        location_id = null;
        position_number = -1;
        depth = "";
        clearInProgress = false;
    }

    onTime_valChanged: {
        if (time_val) {
            console.debug("time_val = '" + time_val + "'");

            // Display the month/day of the date, but not the year.
            var mdy_minhr_str = String(CommonUtil.get_date_str(time_val));
            // Strip out the year field for displaying.
            var year_text = String(time_val.getFullYear());  // Assume: always 4 digits.
            tfTime.text = mdy_minhr_str.replace("/" + year_text, "");

            console.debug("tfTime.text (no year) ='" + tfTime.text + "'");
        } else {
            tfTime.text = ""
        }
    }

    onRejected: {
        console.info("Rejected changes to GPS.");
        clear();
    }
    onAccepted: {
        console.info("Accepted changes to GPS.");
    }



    Component.onCompleted: {
        tfTime.forceActiveFocus();
        // Disable the OK button - all fields empty at this point.
        enable_OK_button_if_required_fields_not_empty();
    }

    contentItem: Rectangle {
        color: "lightgray"

        GridLayout { // Label+Time / NumPad+(Lat/Long/Depth) / Done+Cancel
            flow: GridLayout.TopToBottom
            rows: 3
            columns: 1
            columnSpacing: 0
            rowSpacing: 0

            anchors.fill: parent

            RowLayout {
                Layout.alignment: Qt.AlignHCenter
                spacing: 50
                FramLabel {
                    id: entry_title
                    text: ""
                }

           }

            RowLayout {    // Time/Lat/Long/Depth on Left, NumPad on Right
                //Layout.margins: 20
                //spacing: 0
                //Layout.alignment: Qt.AlignHCenter

                GridLayout { // Time/Latitude/Longitude/Depth
                    rows: 5
                    columns: 1
                    flow: GridLayout.TopToBottom
                    columnSpacing: 0
                    rowSpacing: 20
                    RowLayout {
                        anchors.left: parent.left
                        FramButton {
                            id: btnGetLatLon
                            text: "Tablet GPS Lat/Lon"
                            Layout.leftMargin: 20
                            implicitWidth: 100
                            onClicked: {
                                appstate.hauls.locations.tabletGPS.getGPSLatLon()
                            }
                        }
                        Label {}  // spacer
                        Label {
                            id: labelGpsStatus
                            text: ""
                            font.pixelSize: 14
                        }
                        Connections {
                            target: appstate.hauls.locations.tabletGPS
                            onStatusChanged: {
                                // pass custom text from python signal
                                labelGpsStatus.text = s
                                labelGpsStatus.color = color
                                labelGpsStatus.font.pixelSize = size
                            }
                        }
                    }
                    RowLayout { // TIME
                        // Give extra row space between Time and Latitude (columns aren't aligned, diff measures)
                        Layout.alignment: Qt.AlignHCenter || Qt.AlignTop
                        Layout.preferredHeight: default_tf_height + 5

                        FramLabel {
                            id: labelTime
                            text: "Time"
                            font.pixelSize: default_fontsize_pixels
                        }

                        TextField {
                            id: tfTime
                            text: ""
                            placeholderText: "m/d h:m"
                            font.pixelSize: default_fontsize_pixels
                            Layout.preferredWidth: 170
                            Layout.preferredHeight: default_tf_height
                            //KeyNavigation.tab: tfLatDeg

                            onActiveFocusChanged:  {
                                if (focus) {
                                    focus = false; // prevent dialog from opening a million times
                                    console.debug("tfTime got focus.");
                                    dateLocationPicker.open();
                                }
                            }
                            onTextChanged: {
                                enable_OK_button_if_required_fields_not_empty();
                                nextItemInFocusChain().forceActiveFocus();
                            }

                            // Debug
                            // Component.onCompleted: console.debug("height=" + height);
                        }

                        FramDatePickerDialog {
                            id: dateLocationPicker
                            enable_audio: numPad.enable_audio
                            onDateAccepted: {
                                console.info("Picked start datetime: " + selected_date);
                                time_val = selected_date;
                            }
                        }
                        Connections {
                            target: appstate.hauls.locations.tabletGPS
                            onTimestampChanged: {
                                time_val = new Date(ts)
                            }
                        }
                    }
                    RowLayout { // LATITUDE
                        spacing: 0
                        FramLabel {
                            text: "Latitude    +"
                            font.pixelSize: default_fontsize_pixels
                        }
                        TextField {
                            id: tfLatDeg
                            text: ""
                            cursorPosition: text.length
                            validator: IntValidator {bottom: 0; top: 90}
                            font.pixelSize: default_fontsize_pixels
                            placeholderText: "\u00B0"
                            Layout.preferredWidth: 50
                            Layout.preferredHeight: default_tf_height

                            onActiveFocusChanged:  {
                                if (focus) {
                                    //console.debug("tfLatDeg got focus.");
                                    numPad.showDecimal(false);
                                    numPad.directConnectTf(this);
                                    cursorPosition  = text.length;
                                    update_current_textfield(this, "tfLatDeg");
                                } else { // User hit "Next" button
                                    // Allow exit of empty field
                                    if (text.length == 0) {
                                        return;
                                    }

                                    // Validate degrees (not yet minutes)
                                    var val_result = validate_degrees("Latitude", tfLatDeg.text);
                                    if (val_result == -1)
                                        return;

                                    if (val_result == 0) {
                                        clear_degrees_and_minutes("Latitude");
                                        return;
                                    }
                                }
                            }

                            onTextChanged: {
                                if (text.length < expected_lat_degree_digits) {
                                    // Wait for two digits
                                    return;
                                }
                                enable_OK_button_if_required_fields_not_empty(); // Do early before early exits.

                                // Validate degrees (not yet minutes)
                                var val_result = validate_degrees("Latitude", tfLatDeg.text);
                                if (val_result == -1)
                                    return;

                                if (val_result == 0) {
                                    clear_degrees_and_minutes("Latitude");
                                    return;
                                }

                                // If 2 valid digits have been entered, advance focus to the next field
                                if (text.length == expected_lat_degree_digits) {
                                    nextItemInFocusChain().forceActiveFocus();
                                }

                                // If minutes are not empty, validate degrees and minutes combined. (e.g "90 deg 1 min")
                                if (minutes_are_not_empty("Latitude")) {
                                    lat_degs = calc_latitude_ddegs();
                                    // Display error pop-up if latitude out-of-range.
                                    val_result = validate_lat(lat_degs);
                                    if (val_result == 0) { // Validation failed; clear both degrees and mins.
                                        clear_degrees_and_minutes("Latitude");
                                        focus = true; // Keep cursor in degree field
                                    }
                                }
                            }
                        }
                        FramLabel {
                            id: labelLatDegreeSymbol
                            text: "\u00B0 "
                            font.pixelSize: default_fontsize_pixels
                            Layout.preferredHeight: default_tf_height
                            verticalAlignment: Text.AlignTop
                        }
                        TextField {
                            id: tfLatMinWhole
                            text: ""
                            cursorPosition: text.length
                            font.pixelSize: default_fontsize_pixels
                            placeholderText: "\'"
                            Layout.preferredHeight: default_tf_height
                            Layout.preferredWidth: 50

                            onActiveFocusChanged: {
                                if (focus) {
                                    numPad.showDecimal(false);
                                    numPad.directConnectTf(this);
                                    cursorPosition  = text.length;
                                    update_current_textfield(this, "tfLatMinWhole");
                                }
                            }
                            onTextChanged: {
                                //console.debug("tfLatMinWhole text =" + tfLatMinWhole.text);

                                enable_OK_button_if_required_fields_not_empty(); // Do early before early exits.

                                var val_result = validate_whole_minutes("Latitude", tfLatMinWhole.text);
                                if (val_result == -1) // Val not performed; skip the rest
                                    return;

                                if (val_result == 0) { // Whole minutes by themselves fail.
                                    clear_minutes("Latitude");
                                    return;
                                }

                                // Validation of minutes field passed. Try both degrees and minutes.
                                lat_degs = calc_latitude_ddegs();
                                // Display error pop-up if latitude out-of-range.
                                val_result = validate_lat(lat_degs);

                                if (val_result == 0) {
                                    clear_degrees_and_minutes("Latitude");
                                    return;
                                }

                                // If 2 valid digits have been entered for minutes, advance focus to the next field
                                if (text.length == expected_minutes_digits) {
                                    nextItemInFocusChain().forceActiveFocus();
                                }
                            }
                        }
                        FramLabel {
                            id: labelLatMinutesDecimalPoint
                            text: "."
                            font.pixelSize: default_fontsize_pixels * 2
                            verticalAlignment: Text.AlignBottom
                        }
                        TextField {
                            id: tfLatMinFract
                            text: ""
                            cursorPosition: text.length
                            font.pixelSize: default_fontsize_pixels
                            placeholderText: "0"
                            Layout.preferredHeight: default_tf_height
                            Layout.preferredWidth: 80
                            // inputMask: "00x0000"

                            // Allow advance to next field if adding text, but don't advance if backspacing.
                            property string prev_text

                            onActiveFocusChanged: {
                                if (focus) {
                                    numPad.showDecimal(false);
                                    numPad.directConnectTf(this);
                                    cursorPosition  = text.length;
                                    // Initialize for tracking user key entry (adding or removing digits)
                                    prev_text = text;
                                    update_current_textfield(this, "tfLatMinFract");
                                } else {
                                    // Truncate to four digits
                                    if (text.length > max_minutes_decimal_places) {
                                        text = text.slice(0, max_minutes_decimal_places);
                                    }
                                    // If non-zero fractional minute but whole minutes are empty, put zero in whole.
                                    if (text > 0 && tfLatMinWhole.text.length == 0) {
                                        tfLatMinWhole.text = "0";
                                    }
                                }
                            }
                            onTextChanged: {
                                // ## Redundant validation?? ##
                                // Try validation of both degrees and minutes, including fractional minutes.
                                lat_degs = calc_latitude_ddegs();
                                // Display error pop-up if latitude out-of-range.
                                var val_result = validate_lat(lat_degs);

                                if (val_result == 0) {
                                    clear_degrees_and_minutes("Latitude");
                                } else {
                                    // Is user adding digits, or removing them? Why does it matter?
                                    // Do advance to next field if digit just added, but not if one just removed.
                                    var just_added_digit = text.length > prev_text.length;
                                    prev_text = text;   // Update now in case we lose focus.
                                    //if (!just_added_digit)
                                      //  console.debug("Just deleted a digit");

                                    // If user just added a second digit fractional minutes,
                                    // advance focus to the next field. But don't if user just deleted a digit.
                                    if (just_added_digit && text.length == expected_minutes_decimal_places) {
                                        nextItemInFocusChain().forceActiveFocus();
                                        // console.debug("Advancing to next field (min decimal places)");
                                    }
                                    // If maximum digits have been entered, advance to the next field
                                    if (text.length == max_minutes_decimal_places) {
                                        nextItemInFocusChain().forceActiveFocus();
                                        // console.debug("Advancing to next field (max decimal places)");
                                    }
                                }
                            }
                        }
                        FramLabel {
                            id: labelLatMinutesSymbol
                            text: "\'"
                            font.pixelSize: default_fontsize_pixels
                            Layout.preferredHeight: default_tf_height
                            verticalAlignment: Text.AlignTop
                        }
                        Connections {
                            target: appstate.hauls.locations.tabletGPS
                            onLatitudeChanged: {
                                tfLatDeg.text = appstate.hauls.locations.tabletGPS.latDegrees
                                tfLatMinWhole.text = appstate.hauls.locations.tabletGPS.latMinutes
                                tfLatMinFract.text = ((appstate.hauls.locations.tabletGPS.latSeconds/60)*100).toFixed(0)
                            }
                        }
                    }
                    RowLayout { // LONGITUDE
                        spacing: 0
                        FramLabel {
                            // Use a hyphen the width of a digit: "figure dash"
                            text: "Longitude  \u2012"
                            font.pixelSize: default_fontsize_pixels
                        }
                        TextField {
                            id: tfLongDeg
                            text: ""
                            cursorPosition: text.length
                            validator: IntValidator {bottom: -180; top: 180}
                            font.pixelSize: default_fontsize_pixels
                            placeholderText: "\u00B0"
                            Layout.preferredWidth: 75 // 3 digits
                            Layout.preferredHeight: default_tf_height
                            // inputMask: "000"
                            onActiveFocusChanged:  {
                                if (focus) {
                                    numPad.showDecimal(false);
                                    numPad.directConnectTf(this);
                                    cursorPosition  = text.length;
                                    update_current_textfield(this, "tfLongDeg");
                                }
                            }
                            onTextChanged: {
                                enable_OK_button_if_required_fields_not_empty(); // Do early before early exits.

                                // Validate degrees (but not yet minutes).
                                var val_result = validate_degrees("Longitude", tfLongDeg.text);
                                if (val_result == -1)
                                    return;

                                if (val_result == 0) {
                                    clear_degrees_and_minutes("Longitude");
                                    return;
                                } else {
                                    // If 3 valid digits have been entered, advance focus to the next field
                                    if (text.length == expected_long_degree_digits) {
                                        nextItemInFocusChain().forceActiveFocus();
                                    }

                                    // If minutes are not empty, validate degrees and minutes combined.
                                    // (e.g. catch "90 deg 1 min")
                                    if (minutes_are_not_empty("Longitude")) {
                                        long_degs = calc_longitude_ddegs();
                                        // Display error pop-up if longitude out-of-range.
                                        val_result = validate_long(long_degs);
                                    }
                                    if (val_result == 0) { // Validation failed; clear both degrees and mins.
                                        clear_degrees_and_minutes("Longitude");
                                        focus = true; // Keep cursor in degree field
                                    }
                                }
                            }
                        }
                        FramLabel {
                            id: labelLongDegreeSymbol
                            text: "\u00B0 "
                            font.pixelSize: default_fontsize_pixels
                            Layout.preferredHeight: default_tf_height
                            verticalAlignment: Text.AlignTop
                        }
                        TextField {
                            id: tfLongMinWhole
                            text: ""
                            cursorPosition: text.length
                            placeholderText: "\'"
                            font.pixelSize: default_fontsize_pixels
                            Layout.preferredHeight: default_tf_height
                            Layout.preferredWidth: 50 // Two digits

                            onActiveFocusChanged: {
                                if (focus) {
                                    numPad.showDecimal(false);
                                    numPad.directConnectTf(this);
                                    cursorPosition  = text.length;
                                    update_current_textfield(this, "tfLongMinWhole");
                                }
                            }
                            onTextChanged: {
                                var val_result = validate_whole_minutes("Longitude", tfLongMinWhole.text);
                                if (val_result == -1) // Val not performed; skip the rest
                                    return;

                                if (val_result == 0) { // Minutes by itself fails
                                    clear_minutes("Longitude");
                                    return;
                                }

                                // If 2 valid digits have been entered for minutes, advance focus to the next field
                                if (text.length == expected_minutes_digits) {
                                    nextItemInFocusChain().forceActiveFocus();
                                }

                                // Validation of whole minutes field passed. Try both degrees and minutes.
                                long_degs = calc_longitude_ddegs();
                                // Display error pop-up if longitude out-of-range.
                                val_result = validate_long(long_degs);

                                if (val_result == 0) {
                                    clear_degrees_and_minutes("Longitude");
                                }
                            }
                        }
                        FramLabel {
                            id: labelLongMinutesDecimalPoint
                            text: "."
                            font.pixelSize: default_fontsize_pixels * 2
                            verticalAlignment: Text.AlignBottom
                        }
                        TextField {
                            id: tfLongMinFract
                            text: ""
                            cursorPosition: text.length
                            font.pixelSize: default_fontsize_pixels
                            placeholderText: "0"
                            Layout.preferredHeight: default_tf_height
                            Layout.preferredWidth: 80
                            // inputMask: "00x0000"

                            // Allow advance to next field if adding text, but don't advance if backspacing.
                            property string prev_text

                            onActiveFocusChanged: {
                                if (focus) {
                                    numPad.showDecimal(false);
                                    numPad.directConnectTf(this);
                                    cursorPosition  = text.length;
                                    // Initialize for tracking user key entry (adding or removing digits)
                                    prev_text = text;
                                    update_current_textfield(this, "tfLongMinFract");
                                } else {
                                    // Truncate to four digits
                                    if (text.length > max_minutes_decimal_places) {
                                        text = text.slice(0, max_minutes_decimal_places);
                                    }
                                    // If non-zero fractional minute but whole minutes are empty, put zero in whole.
                                    if (text > 0 && tfLongMinWhole.text.length == 0) {
                                        tfLongMinWhole.text = "0";
                                    }
                                }
                            }
                            onTextChanged: {
                                // ## REDUNDANT VALIDATION? ##
                                // Try validation of both degrees and minutes, including fractional minutes.
                                long_degs = calc_longitude_ddegs();
                                // Display error pop-up if longitude out-of-range.
                                var val_result = validate_long(long_degs);

                                if (val_result == 0) {
                                    clear_degrees_and_minutes("Longitude");
                                } else {

                                    // Is user adding digits, or removing them? Why does it matter?
                                    // Do advance to next field if digit just added, but not if one just removed.
                                    var just_added_digit = text.length > prev_text.length;
                                    prev_text = text;   // Update now in case we lose focus.

                                    // If user just added a second digit fractional minutes,
                                    // advance focus to the next field. But don't if user just deleted a digit.
                                    if (just_added_digit && text.length == expected_minutes_decimal_places) {
                                        nextItemInFocusChain().forceActiveFocus();
                                        //console.debug("Advancing to next field (min decimal places)");
                                    }
                                    // If maximum digits have been entered, advance to the next field
                                    if (text.length == max_minutes_decimal_places) {
                                        nextItemInFocusChain().forceActiveFocus();
                                        //console.debug("Advancing to next field (max decimal places)");
                                    }
                                }
                            }
                        }
                        FramLabel {
                            id: labelLongMinutesSymbol
                            text: "\'"
                            font.pixelSize: default_fontsize_pixels
                            Layout.preferredHeight: default_tf_height
                            verticalAlignment: Text.AlignTop
                        }
                        Connections {
                            target: appstate.hauls.locations.tabletGPS
                            onLongitudeChanged: {
                                tfLongDeg.text = Math.abs(appstate.hauls.locations.tabletGPS.lonDegrees)
                                tfLongMinWhole.text = appstate.hauls.locations.tabletGPS.lonMinutes
                                tfLongMinFract.text = ((appstate.hauls.locations.tabletGPS.lonSeconds/60)*100).toFixed(0)
                            }
                        }
                    }
                    RowLayout { // DEPTH
                        FramLabel {
                            text: "Depth (ftm)"  // 11-Oct-2016: Neil Riley said u/m are fathoms, not meters.
                            font.pixelSize: default_fontsize_pixels
                        }
                        TextField {
                            id: tfDepth
                            text: ""
                            cursorPosition: text.length
                            font.pixelSize: default_fontsize_pixels
                            placeholderText: "Fathoms"
                            Layout.preferredWidth: 100
                            Layout.preferredHeight: default_tf_height

                            // Allow advance to next field if adding text, but don't advance if backspacing.
                            property string prev_text

                            // inputMask blows away placeHolderText. Use validator instead.
                            //inputMask: "000x00" // Optionally allow two decimal places
                            validator: DoubleValidator {
                                bottom: 0.00; top: 999.99; decimals: 2;
                                notation: DoubleValidator.StandardNotation
                            }
                            onActiveFocusChanged:  {
                                text = round_numeric_txt_to_max_decimals(text, max_depth_decimal_places);
                                if (focus) {
                                    numPad.showDecimal(true);
                                    numPad.directConnectTf(this);
                                    cursorPosition  = text.length;
                                    // Initialize for tracking user key entry (adding or removing digits)
                                    prev_text = text;
                                    update_current_textfield(this, "tfDepth");
                                } else {
                                    /**** TODO: GET THIS WORKING WITHOUT DISABLING ABILITY TO CLICK ON ANOTHER FIELD
                                    // Move focus to OK dialog button if validation passes
                                    tfDepth.focus = false;
                                    btnOK.focus = true;
                                    ****/
                                }
                            }
                            onTextChanged: {
                                validate_depth();
                                enable_OK_button_if_required_fields_not_empty();

                                /*********************
                                var just_added_digit = text.length > prev_text.length;
                                prev_text = text; // Update now in case we lose focus.
                                if (!just_added_digit)
                                    console.debug("Just deleted a digit");

                                // ## TODO: Re-factor this quick-and-dirty
                                // If user has entered the max number of digits or more,
                                // truncate to max digits and advance focus to OK
                                var input_length = text.length;
                                if (just_added_digit) {
                                    var maximum_text = String(parseFloat(text).toFixed(
                                            max_depth_decimal_places));
                                    if (input_length >= maximum_text.length) {
                                        // Advance to OK button
                                        tfDepth.focus = false;
                                        btnOK.focus = true;
                                    }
                                }
                                ****************************/
                            }
                            Connections {
                                target: appstate.hauls.locations.tabletGPS
                                onFocusDepthField: {
                                    tfDepth.forceActiveFocus()
                                }
                            }
                        }
                    }

                    ////
                    // Pop-up Dialogs - Triggered by GridLayout components, but not part of grid.
                    ////
                    FramNoteDialog {
                        id: dlgMinutesTooLarge
                        property string component_offended
                        property string offending_minutes
                        message: dlgMinutesTooLarge.component_offended
                            + " minutes of " + offending_minutes
                            + "\nis not less than 60."
                    }

                    FramNoteDialog {
                        id: dlgLatOrLongOutOfRange
                        // Properties assumed to be defined:
                        //      component_offended,
                        //      offending_value
                        //      polarity_offended,
                        //      bound_offended
                        property string component_offended
                        property string offending_value
                        property string polarity_offended
                        property string bound_offended

                        message: dlgLatOrLongOutOfRange.component_offended + " "
                            + dlgLatOrLongOutOfRange.offending_value
                            + "\nis "
                            + dlgLatOrLongOutOfRange.polarity_offended + " than "
                            + dlgLatOrLongOutOfRange.bound_offended + " degrees."
                        font_size: 18
                    }

                    FramNoteDialog {
                        id: dlgDepthTooGreat
                        property string invalidDepth
                        message: "Depth of " + invalidDepth +
                                " exceeds " + trawl_max_depth_fathoms + " fathoms.\n" +
                                "Please ensure fishing depth,\n" +
                                "not bottom depth, is recorded."
                        font_size: 18
                        //forceActiveFocus()
                    }
                }
                Rectangle { // NUMPAD
                    color: "lightgray"
                    Layout.fillHeight: true
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignCenter
                    FramScalingNumPad {
                        id: numPad
                        anchors.fill: parent

                        // Numpad is currently not responding to request to turn off activeFocusOnTab.
                        // TODO: Get this working (may require change to FramScalingNumPad)
                        // Purpose: avoid "Next" while in Depth textfield to "CLR" button of numpad.
                        activeFocusOnTab: false; // Don't include in focus chain (for auto advance and retreat)

                        direct_connect: true
                        leading_zero_mode: true
                        btnOk.text: "Next"
                        enable_audio: false

                        property int tfLengthAfterLastKeyPress : 0

                        onDirectConnectTf: {
                            tfLengthAfterLastKeyPress = connect_tf.text.length;
                            //console.debug("Connected to new text field with length=" + tfLengthAfterLastKeyPress);
                        }

                        onNumpadok: {
                            // next item in tab order
                            connect_tf.nextItemInFocusChain().forceActiveFocus();
                        }
                        onNumpadinput: {
                            tfLengthAfterLastKeyPress = connect_tf.text.length;
                            //console.debug("Numeric key pressed, field length now = " + tfLengthAfterLastKeyPress);
                        }

                        onBackspacenumpad: {
                            // Retreat to previous text field when backspace is hit when the field is already empty,
                            // (but don't jump to previous field when a backspace clears the last digit).
                            if (tfLengthAfterLastKeyPress == 0) {
                                var backwards = false;
                                connect_tf.nextItemInFocusChain(backwards).forceActiveFocus();
                                console.debug("Backspace hit on empty field - retreating one field");
                            } else {
                                tfLengthAfterLastKeyPress = connect_tf.text.length;
                            }
                        }

                        onClearnumpad: {
                            console.debug("CLR pressed on text field '" + current_textfield_name + "'" +
                                "; re-establishing directConnectTf.");
                            // Re-establish connection to this field to avoid extra 0
                            numPad.directConnectTf(current_textfield);
                        }
                    }
                }
            }

            RowLayout { // OK/Cancel Buttons
                id: dialogExitButtons
                Layout.alignment: Qt.AlignHCenter
                spacing: 20

                FramButton {
                    id: btnCancel
                    text: "Cancel"
                    fontsize: 18
                    onClicked: {
                        dlg.reject();
                    }
                }

                FramButton {
                    id: btnOK
                    // OK to use "OK" for dialog dismissal since numpad "OK" is re-labeled "Next"
                    text: "OK"
                    fontsize: 18
                    onClicked: {
                        if (tfLatDeg.text.length > 0 &&
                                tfLongDeg.text.length > 0 &&
                                tfDepth.text.length > 0 &&
                                tfTime.text.length > 0) {
                            // For the benefit of the screen invoking this dialog,
                            // set numeric fields that may be empty to zero.
                            tfLatMinWhole.text = (tfLatMinWhole.text.length > 0) ? tfLatMinWhole.text: "0";
                            tfLatMinFract.text = (tfLatMinFract.text.length > 0) ? tfLatMinFract.text: "0";
                            tfLongMinWhole.text = (tfLongMinWhole.text.length > 0) ? tfLongMinWhole.text: "0";
                            tfLongMinFract.text = (tfLongMinFract.text.length > 0) ? tfLongMinFract.text: "0";

                            // Don't store more than the maximum decimal digits.
                            tfDepth.text = round_numeric_txt_to_max_decimals(tfDepth.text, max_depth_decimal_places);

                            // Check if this is a duplicate location
                            if (!appstate.hauls.locations.verifyNoMatchGPSPosition(position_number, lat_degs, long_degs)) {
                                // TODO warning, override OK
                                dlgMatchingLocations.open();
                                return;
                            } else if (parseFloat(tfDepth.text) <= 0) { // FIELD-2079: deny 0 depth vals
                                dlgBadDepthVal.open()
                                return
                            } else {
                                dlg.accept();
                            }
                        }
                    }

                    states: [
                        State {
                            name: "enabled" // All needed fields have been filled in
                            PropertyChanges {
                                target: btnOK
                                enabled: true
                                text_color: "black"
                                bold: true
                                //grdTopColor: "white"
                                //grdBottomColor: "#eee"
                            }
                        },
                        State {
                            name: "disabled"
                            PropertyChanges {
                                target: btnOK
                                enabled: false
                                text_color: "gray"
                                bold: false
                                //grdTopColor: "lightgray"
                                //grdBottomColor: "lightgray"
                                //grdTopColor: "#ccc"
                                //grdBottomColor: "#ccc"
                            }
                        }
                    ]
                }
            }
        }
        ProtocolWarningDialog {
            id: dlgMatchingLocations
            message: "Warning! The lat/longitude entered is an\nexact match with another.\nPlease double check the logbook.";
            onRejected: {
                // Acknowledged that this is OK
                dlg.accept()
                console.warn("Allowed matching GPS locations.");
                if (ObserverSettings.enableAudio) {
                    soundPlayer.play_sound("keyOK", false);
                }
            }
        }
        FramNoteDialog {
            // FIELD-2079: used to deny depth values = 0
            id: dlgBadDepthVal
            title: "Bad Depth Value"
            bkgcolor: "#FA8072"
            message: "Error! Depth values <= 0\nnot allowed, please resolve."
        }
        Keys.onEscapePressed: dlg.reject()
        Keys.onBackPressed: dlg.reject()
    }
}
