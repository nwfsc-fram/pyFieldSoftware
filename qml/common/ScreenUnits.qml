pragma Singleton

import QtQuick 2.5

QtObject {
    id: screenUnitsSingleton

    // FramNumPad units
    property int numPadButtonTextHeight: 20
    property int numPadButtonSize: 85  // Width and Height

    // FramKeyboard units
    property int keyboardButtonTextHeight: 25

}
