pragma Singleton

import QtQuick 2.5

// Utility singleton for common classes
QtObject {
    id: commonControlSingleton

    // For FramSlidingKeyboard:
    property int active_kb_count: 0 // "Ref count" for users using sliding keyboard - track visibility

    // Logging Functions- fall back to console if framlog isn't defined
    function debug(logstr) {
        try {
            framlog.debug(logstr);
        }
        catch(err) {
            console.debug(logstr);
        }
    }
    function log(logstr) {
        try {
            framlog.info(logstr);
        }
        catch(err) {
            console.info(logstr);
        }
    }
    function info(logstr) {
        try {
            framlog.info(logstr);
        }
        catch(err) {
            console.info(logstr);
        }
    }
    function warning(logstr) {
        try {
            framlog.warning(logstr);
        }
        catch(err) {
            console.warn(logstr);
        }
    }
    function error(logstr) {
        try {
            framlog.error(logstr);
        }
        catch(err) {
            console.error(logstr);
        }
    }

    // Utility functions: console log an error if framutil not declared in root context
    function get_fraction(test) {
        try {
            return framutil.get_fraction(test);
        }
        catch(err) {
            console.error("Could not access framutil object (not in root context?) " + err);
        }
    }

    // Date Functions

    function get_date_str(dateobj) {
            // Return from a Date object a U.S.-friendly string in this format: MM/dd/yyyy hh:mm.
            // Single digit months, days, hours, and minutes are zero-padded.
            if (!dateobj) {
                console.error("get_date_str got a bad date object.")
                return null
            }

            var min_text = String(dateobj.getMinutes());
            var min_padding = min_text.length > 1 ? "" : "0";
            var hour_text = String(dateobj.getHours());
            var hour_padding = hour_text.length > 1 ? "" : "0";
            var day_text = String(dateobj.getDate());
            var day_padding = day_text.length > 1 ? "" : "0";
            // Months are zero-relative; add one.
            var month_text = String(dateobj.getMonth() + 1);
            var month_padding = month_text.length > 1 ? "" : "0";
            var year_text = String(dateobj.getFullYear());  // Assume: always 4 digits.
            var date_str = month_padding + month_text + "/" +
                        day_padding + day_text + "/" +
                        year_text + " " +
                        hour_padding + hour_text + ":" +
                        min_padding + min_text;
            console.debug("Date string = '" + date_str + "'");
            return date_str;
        }

    // Test Functions

    function assertEquals(var1, var2, errmsg) {
        errmsg = errmsg || ""
        if (var1 != var2) {  // might be equal via type coercion
            console.error("assertEquals failed: " + var1 + " != " + var2 + " " + errmsg);
            quitApp("Test failed.");
        }
    }

    function assertGreater(var1, var2, errmsg) {
        errmsg = errmsg || ""
        if (var1 <= var2) {
            console.error("assertGreater failed: " + var1 + " <= " + var2 + " " + errmsg);
            quitApp("Test failed.");
        }
    }

    function assertGreaterEq(var1, var2, errmsg) {
        errmsg = errmsg || ""
        if (var1 < var2) {
            console.error("assertGreaterEq failed: " + var1 + " < " + var2 + " " + errmsg);
            quitApp("Test failed.");
        }
    }

    function assertLess(var1, var2, errmsg) {
        errmsg = errmsg || ""
        if (var1 >= var2) {
            console.error("assertLess failed: " + var1 + " <= " + var2 + " " + errmsg);
            quitApp("Test failed.");
        }
    }

    function assertLessEq(var1, var2, errmsg) {
        errmsg = errmsg || ""
        if (var1 > var2) {
            console.error("assertLessEq failed: " + var1 + " <= " + var2 + " " + errmsg);
            quitApp("Test failed.");
        }
    }

    function assertTrue(var1, errmsg) {
        errmsg = errmsg || ""
        if (!var1) {
            console.error("assertTrue failed: " + errmsg);
            quitApp("Test failed.");
        }
    }

    function assertFalse(var1, errmsg) {
        errmsg = errmsg || ""
        if (var1) {
            console.error("assertFalse failed: " + errmsg);
            quitApp("Test failed.");
        }
    }

    function quitApp(msg) {
        console.warn("Quitting application. " + msg);
        Qt.quit();
    }

    function copySign(val, sign_val) {
        // Apparently there isn't a JS Math.copySign
        if (sign_val < 0)
            return -1 * Math.abs(val);
        else
            return Math.abs(val);
    }

    function calc_decimal_degs(degrees, decmins) {
        // console.debug("calc_decimal_degs: degs=" + degrees + " mins=" + decmins);
        var decimal_degrees = degrees + copySign(decmins / 60.0, degrees);
        return decimal_degrees;
    }

    function getDecimalMinutesStr(minuteFloat, includeLeadingZero, nDecimalPlaces) {
        // Latitude and Latitude in Locations are expressed as a whole number number of degrees.
        // Lat/Long minutes are decimal (whole-number/fraction).
        // This utility returns decimal minutes with the number of decimal places specified and
        // a leading zero, if requested and minutes are one digit.
        var minuteStr = minuteFloat.toFixed(nDecimalPlaces);
        if (includeLeadingZero && (minuteStr.length < (3 + nDecimalPlaces))) { // 3: decimal point + 2 digits
            minuteStr = "0" + minuteStr;
        }
        return(minuteStr);
    }
}
