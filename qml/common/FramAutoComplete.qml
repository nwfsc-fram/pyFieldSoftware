import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Controls.Private 1.0

import "." // Needed for CommonUtil

Rectangle {
    id: acRect
    signal clickedautoedit(string editstr) // mouse click handler, with currently selected string

    signal autocomplete_active(bool ac_active)
    onAutocomplete_active: {
        if(ac_active)
            autocomplete.clear_suggestions();  // Default behavior
    }

    signal showautocompletebox(bool show)
    onShowautocompletebox: {
        acRect.height = show ? ac_preferred_textfield_height + ac_preferred_scrollbox_height : ac_preferred_textfield_height;
        is_expanded = show;
        acListView.visible = is_expanded;
        tfAutoCorrect.focus = show; // hides cursor when text input complete
    }

    function addAutoCompleteSuggestions(partialstr) {
        // Perform AutoComplete here
        acModel.clear();
        if (partialstr.length > 0) {
            // console.debug("* Called addAutoCompleteSuggestions for " + partialstr);
            autocomplete.search(partialstr);
            var suggestions = autocomplete.suggestions;
            console.log("Got suggestions " + suggestions);
            for (var i = 0; i< autocomplete.suggestions.length; i++) {
                acModel.append({searchresult: autocomplete.suggestions[i]});
            }
            acListView.focus = true;
        }
    }

    property int ac_preferred_textfield_height: 80
    property int ac_preferred_scrollbox_height: 120
    property bool is_expanded: false

    width: parent.width/2 - 10
    height: ac_preferred_textfield_height

    // Expose the TextField component for external keyboards etc
    property TextField ac_tf: tfAutoCorrect

    function needs_keyboard() {
        // Determine whether we need an onscreen keyboard to be shown, controlled by focus
        return CommonUtil.active_kb_count > 0;
    }

    Column {
        anchors.fill: parent

        TextField {
            id: tfAutoCorrect
            height: ac_preferred_textfield_height
            width: parent.width
            font.pixelSize: 25
            onFocusChanged: {
                if(focus)
                    CommonUtil.active_kb_count++;
                else
                    CommonUtil.active_kb_count--;

                showautocompletebox(focus);
                autocomplete_active(focus);
            }

            onTextChanged: {
//                console.log("AC text " + text);
                addAutoCompleteSuggestions(text);
            }
        }
        Rectangle {
            id: acBorderRect
            height: ac_preferred_scrollbox_height
            width: parent.width
            visible: is_expanded
            border.color: "gray"
            border.width: 1

            ScrollView {
                height: ac_preferred_scrollbox_height
                width: parent.width
                ListView {
                    id: acListView
                    height: ac_preferred_scrollbox_height
                    width: parent.width
                    visible: is_expanded


                    model: ListModel {
                        id: acModel
                    }

                    delegate: Text {

                        text: searchresult
                        font.pixelSize: 25
                        MouseArea {
                            id: resultArea
                            anchors.fill: parent
                            onClicked: {
                                acListView.currentIndex = index;
                                var selected_text = acModel.get(acListView.currentIndex).searchresult
                                console.debug( selected_text + ' selected')
                                tfAutoCorrect.text = selected_text
                            }
                        }
                    }


                    // Interesting effect, don't want it...
    //                highlight: Rectangle {
    //                    color: 'lightgray'
    //                }

                    onCurrentItemChanged: {
                        var selected_text = acModel.get(acListView.currentIndex).searchresult
                        console.debug( selected_text + ' selected')
                    }

                }

            }
        }



    }
}
