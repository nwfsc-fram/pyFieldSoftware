import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Controls.Private 1.0
import QtQuick.Layouts 1.2
import QtQml.Models 2.2
import FramTreeItem 1.0

import "../common"

Item {

    Connections {
        target: stateMachine
        onHaulSelected: { updateSpeciesLists() }
    }
    Connections {
        target: tvAvailableSpecies.selection
        onSelectionChanged: avSelectionChanged()
    }

    Connections {
        target: tvSelectedSpecies.selection
        onSelectionChanged: seSelectionChanged()
    } // tvSelectedSpecies.selection.onSelectionChanged

    Connections {
        target: tvSelectedSpecies
        onExpanded: seExpanded(index)
    }
    Connections {
        target: tvSelectedSpecies
        onCollapsed: seCollapsed(index)
    }

    Connections {
        target: btnFishSampling
        onClicked: fishSamplingClicked()
    }

    signal resetfocus()
    onResetfocus: {
        tvAvailableSpecies.forceActiveFocus()
    }

    Keys.forwardTo: [keyboard]

    Component.onCompleted: {
        main.title = qsTr("Field Collector - Trawl Survey - Backdeck - Process Fish");
//        msg.show('Species count: ' + processCatch.species.length + '\nSample: ' +
//                processCatch.species[0]['display name'])
        keyboard.showbottomkeyboard(false);
        keyboard.connect_tf(tfSpecies);
//        updateHaulDetails()
        updateSpeciesLists()

    }

    Component.onDestruction: {
        tbdSM.to_home_state()
    }

    function fishSamplingClicked() {
        if (stateMachine.species["protocol"]["displayName"] == null)
            dlgConfirm.show("This species does not\nhave a protocol.\nDo you want to sample it?", "no protocol")
        else
            loadSamplingScreen()
    }

    function loadSamplingScreen() {
        if (!screens.busy) {
            if (btnFishSampling.text.indexOf("Fish") > -1) {
                screens.push(Qt.resolvedUrl("FishSamplingScreen.qml"))
                tbdSM.to_fish_sampling_state()
            } else if (btnFishSampling.text.indexOf("Salmon") > -1) {
                screens.push(Qt.resolvedUrl("SalmonSamplingScreen.qml"))
                tbdSM.to_salmon_sampling_state()
            } else if (btnFishSampling.text.indexOf("Coral") > -1) {
                screens.push(Qt.resolvedUrl("CoralSamplingScreen.qml"))
                tbdSM.to_corals_sampling_state()
            }
        }
    }

    function seExpanded(index) {
        var item = tvSelectedSpecies.model.getItem(index)
        item.isExpanded = true
    }

    function seCollapsed(index) {
        var item = tvSelectedSpecies.model.getItem(index)
        item.isExpanded = false
    }

    function sortTreeView(index) {

        var seModel = tvSelectedSpecies.model
        var displayNameNum = seModel.getRoleNumber("displayName")
        var displayName = seModel.data(index, displayNameNum)
        var item = seModel.getItem(index)
        var parentItem = seModel.parent(index)
        var typeRoleNum = seModel.getRoleNumber("type")
        var currentType = seModel.data(index, typeRoleNum)

        // Sort the data using the sortCatch method
        var expandedList = seModel.sortCatch()

        // Expand the newly sorted FramTreeModel
        for (var i=0; i< expandedList.length; i++) {
            tvSelectedSpecies.expand(expandedList[i])
        }

        // Reselect the item that was selected before the sort
        var newIndex = seModel.index(item.row, 0, parentItem)
        tvSelectedSpecies.selModel.setCurrentIndex(newIndex, 0x0002 | 0x0010);

        // Expand the currently selected item if it was a mix or submix
        if ((currentType == "Mix") || (currentType == "Submix")) {
            tvSelectedSpecies.expand(newIndex)
        }
    }

    function seSelectionChanged() {

        var index = tvSelectedSpecies.selModel.currentIndex
//        var typeRoleNum = processCatch.SelectedSpeciesModel.getRoleNumber("type")
//        var type = tvSelectedSpecies.model.data(index, typeRoleNum)
//        var parent;
//        if ((type) && ((type == "Mix") || (type == "Submix"))) {
//            parent = tvSelectedSpecies.model.getItem(index.parent)
//        } else {
//            parent = tvSelectedSpecies.model.rootItem
//        }
//        processCatch.selectedIndex = {"currentIndex": index,
//            "row": index.row, "parent": parent, "type": type};

        processCatch.selectedIndex = {"currentIndex": index};

//        processCatch.selectedIndex = index;
//        console.info('selectedIndex: ' + processCatch.selectedIndex)

        if (index.row == -1) { // No row is selected, disable all buttons and return
            btnRemoveSpecies.state = qsTr("disabled")
            btnWeighBaskets.state = qsTr("disabled")
            btnFishSampling.state = qsTr("disabled")
            btnSpecialAction.state = qsTr("disabled")
            btnCreateMix.state = qsTr("enabled")

            stateMachine.species = null;
            stateMachine.specimen = {"parentSpecimenId": null, "row": -1};

            return;
        }

        // Reset FishSamplingScreen.qml to Sex-Length mode
        fishSampling.mode = "Sex-Length"

        var parentIdx = tvSelectedSpecies.model.parent(index)
        var roleNum = tvSelectedSpecies.model.getRoleNumber("type")
        var childType = tvSelectedSpecies.model.data(index, roleNum)
        var parentType = tvSelectedSpecies.model.data(parentIdx, roleNum)
        var taxonRole = tvSelectedSpecies.model.getRoleNumber("taxonomyId")
        var taxonId = tvSelectedSpecies.model.data(index, taxonRole)

//        console.info('roleNum: ' + roleNum)
//        console.info('childType: ' + childType)
//        console.info('parentType: ' + parentType)

        // Set the selected species
        var catchRole = tvSelectedSpecies.model.getRoleNumber("catchId")
        var catchId = tvSelectedSpecies.model.data(index, catchRole)
        stateMachine.species = catchId

//        console.info('catchId: ' + catchId)

        // Clear the selected specimen
        stateMachine.specimen = {"parentSpecimenId": null, "row": -1};

        // Enable the remove button for removing species
        btnRemoveSpecies.state = qsTr("enabled")

        // Enable/Disable mix creation depending upon the parent/child type
        if ((childType == "Submix") || (parentType == "Submix") || (parentType == "Mix"))
            btnCreateMix.state = qsTr("disabled")
        else {
            btnCreateMix.state = qsTr("enabled")
        }

        // Enable/Disable further actions
        if (childType == "Taxon") {

            btnWeighBaskets.state = qsTr("enabled")
            btnSpecialAction.state = qsTr("enabled")

            // Change FishSampling Label / Action if Salmon or Coral Species
            if (typeof taxonId != 'undefined') {
                var isSalmon = processCatch.checkSpeciesType("salmon", taxonId)
                var isCoral = processCatch.checkSpeciesType("coral", taxonId)
                var isSponge = processCatch.checkSpeciesType("sponge", taxonId)

                if ((isSalmon) || (isCoral) || (isSponge)) {
                    btnFishSampling.state = qsTr("disabled")
                } else {
                    btnFishSampling.state = qsTr("enabled")
                }
            } else {
                btnFishSampling.state = qsTr("disabled")
            }

        } else if ((childType == "Mix") || (childType == "Submix")) {

            btnWeighBaskets.state = qsTr("enabled")
            btnFishSampling.state = qsTr("disabled")
            btnSpecialAction.state = qsTr("disabled")

        } else if (childType == "Debris") {

            btnWeighBaskets.state = qsTr("enabled")
            btnFishSampling.state = qsTr("disabled")
            btnSpecialAction.state = qsTr("disabled")

        }

    }

    function avSelectionChanged() {
        if ((tvAvailableSpecies.selection.count < 1) & btnAddSpecies.state == qsTr("enabled"))
            btnAddSpecies.state = qsTr("disabled")
        else
            btnAddSpecies.state = qsTr("enabled")
    }

    function updateHaulDetails() { tfHaulId.text = stateMachine.haul['haul_number'] }

    function updateSpeciesLists() { var speciesList = processCatch.get_species_per_haul() }

    function filter_species(species_text) { processCatch.filter_species(species_text); }

    function toggleSpeciesList(list) {
        if (list == "full") {
            tvAvailableSpecies.model = processCatch.FullAvailableSpeciesModel
            processCatch.currentSpeciesModel = processCatch.FullAvailableSpeciesModel
        } else if (list == "recent") {
            tvAvailableSpecies.model = processCatch.MostRecentAvailableSpeciesModel
            processCatch.currentSpeciesModel = processCatch.MostRecentAvailableSpeciesModel
        } else if (list == "debris") {
            tvAvailableSpecies.model = processCatch.DebrisModel
            processCatch.currentSpeciesModel = processCatch.DebrisModel
        }
    }

    function removeSpecies()  {

        var seModel = tvSelectedSpecies.model

        // Get the highlighted SelectedSpecies item
        var roleNum = processCatch.SelectedSpeciesModel.getRoleNumber("taxonomyId")
        var idx = tvSelectedSpecies.selModel.currentIndex
        var taxonomyId = tvSelectedSpecies.model.data(idx, roleNum)

        var typeNum = processCatch.SelectedSpeciesModel.getRoleNumber("type")
        var type = tvSelectedSpecies.model.data(idx, typeNum)

        var displayNameNum = processCatch.SelectedSpeciesModel.getRoleNumber("displayName")
        var displayName = tvSelectedSpecies.model.data(idx, displayNameNum)

        // Add to tvAvailableSpecies first (otherwise index is one off)
        processCatch.add_list_item(idx)
        var item = tvSelectedSpecies.model.getItem(idx)

        // Remove from the model._descendantSpecies list
        seModel.remove_descendant(idx)

        // If a mix, reduce the mixCount
        var parentIdx;
        if ((type == "Mix") || (type == "Submix")) {
            parentIdx = idx.parent
            tvSelectedSpecies.model.subtractMixCount(type, displayName, parentIdx)
        }

        // Remove the actual tree item
        processCatch.remove_tree_item(idx)

        if ((type == "Mix") || (type == "Submix")) {
            processCatch.renameMixes()
        }

        // Resort the view
        sortTreeView(idx)

        // Get the updated idx, now that the previous species was removed, if nothing is highlighted
        // then disable the RemoveSpecies button
        idx = tvSelectedSpecies.selModel.currentIndex
        if (idx.row == -1) {
            btnRemoveSpecies.state = qsTr("disabled")
        }
    }

    function addSpecies(addToMix) {

        var seModel = tvSelectedSpecies.model
        var avModel = tvAvailableSpecies.model

        var taxonIdColNum = processCatch.SelectedSpeciesModel.getColumnNumber("taxonomyId")
        var typeRoleNum = processCatch.SelectedSpeciesModel.getRoleNumber("type")
        var parent;
        var type;
        var currentIndex;
        if (!addToMix) {
            // Get the highlighted SelectedSpecies item
            currentIndex = tvSelectedSpecies.selModel.currentIndex
            type = "Taxon"
        } else {
            // Get the procesCatch.activeMix catchId and find the appropriate mix for adding in the values
            var catchIdRole = seModel.getRoleNumber("catchId");
            var catchId = processCatch.activeMix["catchId"];
            if (catchId !== null) {
                currentIndex = seModel.get_index_by_role_value("catchId", catchId);
                currentIndex = seModel.index(currentIndex.row, 0, currentIndex.parent)
            } else {
                console.info('Active mix is not defined, yet you are trying use AddToMix to add to the mix');
                return;
            }
            type = "Mix"
        }
        var idx = []
        var child;
        var taxonId;
        var taxonIdFound;
        var lastTaxonIdAdded;
        var lastDisplayNameAdded;
        var lastItemType;
        var availableItem;
        var availableTaxonId;
        var displayName;
        var modelItem;
        var firstRow = -1;

        // 2019 Bizzarro skates special project ....
        var haulDepth = stateMachine.haul["depth"];
        console.info("haulDepth = " + haulDepth);
        var bizzarroSkates = [42, 44, 49];
        var availableListRow = -1;

        tvAvailableSpecies.selection.forEach(
            function(rowNum) {
                availableListRow = rowNum;

                if (firstRow == -1)
                    firstRow = rowNum;

                // Get the taxonomyId of the selected item in tvAvailableSpecies
                availableItem = avModel.get(rowNum)
                availableTaxonId = availableItem.taxonomyId;
                displayName = availableItem.displayName;

                // Check if the species with this taxonomyId already has been selected,
                // at the parent level (i.e. at the rootItem or within the tvSelectedSpecies selected mix
                // if so, don't add it, just select it in the tvSelectedSpecies model
                // Go through the children of the current parent, only push to the idx list when
                // the taxonomy_id does not equal the child taxonomy_id

//                console.info('availableItem = ' + JSON.stringify(availableItem));

                taxonIdFound = false

                for (var i=0; i<seModel.descendants.length; i++) {
                    taxonId = seModel.descendants[i];
                    if (taxonId == availableTaxonId) {
                        lastTaxonIdAdded = availableTaxonId;
                        lastDisplayNameAdded = displayName;
                        taxonIdFound = true;
                        break;
                    }
                }

                if (!taxonIdFound) {

                    // Bizzarro 2019 special project
                    // taxonIDs = 44 (california), 42 (big skate), 49 (starry skate)
//                    if (bizzarroSkates.indexOf(availableTaxonId) > -1) {
//                        dlgOkay.message = "Welcome to Bizzarro skate country, haul depth = " + haulDepth + "m"
//                        if ((haulDepth > 300) && (haulDepth < 500)) {
//                            dlgOkay.message += "\n\nYou need to take sex, length, and two photos"
//                        } else if (haulDepth >= 500) {
//                            dlgOkay.message += "\n\nYou need to take the sex, length, two photos\nand freeze the skate";
//                        }
//                        dlgOkay.open();
//                    }


                    processCatch.append_tree_item_with_sql(availableItem, currentIndex, type);
                    lastTaxonIdAdded = availableTaxonId;
                    lastDisplayNameAdded = displayName;
                    lastItemType = availableItem.type;
                    idx.push(rowNum);

                    if (btnRemoveSpecies.state == qsTr("disabled"))
                        btnRemoveSpecies.state = qsTr("enabled")
                }
            }
        )

        // Sort the FramTreeView
        sortTreeView(currentIndex)

        // Expand the currently selected item if it was a mix or submix
//        if ((type == "Mix") || (type == "Submix")) {
//            var item = seModel.getItem(currentIndex)
//            var parentItem = seModel.parent(currentIndex)
//            var newIndex = seModel.index(item.row, 0, parentItem)
//            tvSelectedSpecies.expand(newIndex)
//        }

        // Create a new index for the last item added
        var newIndex;
        if (lastItemType === "Debris") {
            lastDisplayNameAdded = "Debris - " + lastDisplayNameAdded;
            newIndex = seModel.get_index_by_role_value("displayName", lastDisplayNameAdded);
            newIndex = seModel.index(newIndex.row, 0, seModel.rootItem)
        } else {
            newIndex = seModel.get_index_by_role_value("taxonomyId", lastTaxonIdAdded);
        }
        console.info('newIndex = ' + newIndex)

        // Scroll to the last item added
        var row = newIndex.row
        if (type == undefined || type == "Taxon" || taxonIdFound) {
        } else if (processCatch.activeMix["displayName"].indexOf("Mix") > -1) {
//        } else if ((type == "Mix") || (processCatch.activeMix["displayName"].indexOf("Mix") > -1)) {
            var parentRow = newIndex.parent.row;
            row = parentRow + row + 1;
        } else if (processCatch.activeMix["displayName"].indexOf("Submix") > -1) {
//        } else if ((type == "Submix") || (processCatch.activeMix["displayName"].indexOf("Submix") > -1)) {
            var submixParentRow = newIndex.parent.row;
            var parentRow = newIndex.parent.parent.row;
            row = parentRow + submixParentRow + row + 1 + 1;
        }
        if (lastItemType === "Debris") {
            tvSelectedSpecies.__listView.positionViewAtEnd();
        } else {
            tvSelectedSpecies.__listView.positionViewAtIndex(row, ListView.Center);
        }

        console.info("activeMix = " + processCatch.activeMix["displayName"] + ", row = " + row + ", lastItemType = " + lastItemType + ", type = " + type);

        // Select the last item added
        tvSelectedSpecies.selModel.setCurrentIndex(newIndex, 0x0002 | 0x0010);

        // Create a reversed index which is used to remove the species from the
        // tvAvailableSpecies TableView.  Use reverse sort order so as to not get an IndexError
        var reverseIdx = []
        reverseIdx = idx.slice()
        reverseIdx.sort(function(a, b) {return b-a})

        // Remove according to the reverse sort otherwise indices become inaccurate
        var item_data
        for (var i = 0; i < reverseIdx.length; i++) {
            item_data = avModel.get(reverseIdx[i])
            processCatch.remove_list_item(item_data)
        }

        // Clear the selection, and reselect the row in the same starting position as before
        // if such as row number exists
        tvAvailableSpecies.selection.clear()

        // Get the display name of the row right after the last availableListRow
        availableItem = avModel.get(availableListRow)
//        availableTaxonId = availableItem.taxonomyId;
        displayName = availableItem.displayName;
        console.info('availableListRow: ' + availableListRow + ', displayName = ' + displayName);

        // Clear the text box
        tfSpecies.text = "";

        // Find the new rowNum with the last displayName
        // Reset to the current position in the tvAvailableSpecies listbox
        availableListRow = avModel.get_item_index("displayName", displayName);
        console.info('new availableListRow: ' + availableListRow);
        tvAvailableSpecies.__listView.positionViewAtIndex(availableListRow, ListView.Center);

    }

    TextField {
        id: tfSpecies
        x: 20
        y: 20
        height: 40
        width: 300
        placeholderText: qsTr("Species Name")
        font.pixelSize: 20
        selectByMouse: true

//       MouseArea {
//            anchors.fill: parent
//            onClicked:{
//                this.focus = false
//                this.cursorShape = Qt.IBeamCursor
//                tfSpecies.forceActiveFocus();
//                if (!keyboard.visible)
//                    keyboard.showbottomkeyboard(true)
//            }
//        }
        onFocusChanged: {
            keyboard.showbottomkeyboard(this.focus)
        }
        onTextChanged: {
            filter_species(this.text);
        }
        Keys.onReturnPressed: {
            keyboard.showbottomkeyboard(false)
            resetfocus()
        }
        Keys.onDownPressed: {
            tvAvailableSpecies.forceActiveFocus()
            tvAvailableSpecies.selection.clear()
            tvAvailableSpecies.selection.select(0)
        }

    } // tfSpecies

    TrawlBackdeckTableView {
        id: tvAvailableSpecies
        x: tfSpecies.x
        y: tfSpecies.y + tfSpecies.height + 10
        width: tfSpecies.width
        height: main.height - tfSpecies.height - 120
        headerVisible: false
        selectionMode: SelectionMode.ExtendedSelection
        horizontalScrollBarPolicy: Qt.ScrollBarAlwaysOff

        model: processCatch.FullAvailableSpeciesModel

//        selection: ItemSelectionModel {
//            id: selectionModel
//            model: tvAvailableSpecies.model
//        }

        onDoubleClicked: {
            addSpecies(false)
        }

        Keys.onReturnPressed: {
            addSpecies(false)
        }

        TableViewColumn {
            role: "displayName"
            title: "Species"
            width: tfSpecies.width
        }
    } // tvAvailableSpecies

    RowLayout {
        x: tvAvailableSpecies.x
        y: tvAvailableSpecies.y + tvAvailableSpecies.height + 10
//        style: Style {
//            property Component panel: Rectangle {
//                color: "transparent"
//                border.width: 0
//            }
//        }
        ExclusiveGroup {
            id: grpList
        }
        TrawlBackdeckButton {
            id: btnFullList
            text: qsTr("Full\nList")
//            x: tvAvailableSpecies.x
//            y: parent.y
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            checked: true
            checkable: true
            exclusiveGroup: grpList
            onClicked: {toggleSpeciesList("full")}
        } // btnFullList
        TrawlBackdeckButton {
            id: btnMostRecentList
            text: qsTr("Most Recent\nList")
//            x: btnFullList.x + btnFullList.width + 10
//            y: parent.y
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            checked: false
            checkable: true
            exclusiveGroup: grpList
            onClicked: {toggleSpeciesList("recent")}
        } // btnMostRecentList
        TrawlBackdeckButton {
            id: btnDebrisList
            text: qsTr("Debris\nList")
//            x: btnFullList.x + btnFullList.width + 10
//            y: parent.y
            Layout.preferredWidth: this.width
            Layout.preferredHeight: this.height
            checked: false
            checkable: true
            exclusiveGroup: grpList
            onClicked: {toggleSpeciesList("debris")}
        } // btnDebrisList
    }

    Column {
        id: colSpeciesControllers
        x: tvAvailableSpecies.x + tvAvailableSpecies.width + 20
        y: 80
        width: 100
        spacing: 60
        TrawlBackdeckButton {
            id: btnAddSpecies
            text: qsTr("Add\n>")
            state: qsTr("disabled")
            onClicked: {
                addSpecies(false)
            }
        } // btnAddSpecies
        TrawlBackdeckButton {
            id: btnRemoveSpecies
            text: qsTr("Remove\n<")
            state: qsTr("disabled")
            onClicked: {
                var index = selModel.currentIndex.row;
                if (index != -1) {
                    var role = processCatch.SelectedSpeciesModel.getRoleNumber("displayName")
                    var name = tvSelectedSpecies.model.data(selModel.currentIndex, role)

                    role = processCatch.SelectedSpeciesModel.getRoleNumber("taxonomyId")
                    var taxonomyId = tvSelectedSpecies.model.data(index, role)
                    var results = processCatch.checkSpeciesForData()

                    if ((results["baskets"] == -1) || (results["specimens"] == -1)) {
                        console.info('problem getting basket / specimen counts')

                    } else if ((results["baskets"] > 0) || (results["specimens"] > 0)) {

                        processCatch.playSound("deleteItem")

                        dlgRemoveSpecies.message = "You are about to remove the following species:\n\n" + name + "\n\n"
                        dlgRemoveSpecies.message += "Basket Count: " + results["baskets"] + "\n"
                        dlgRemoveSpecies.message += "Specimen Count: " + results["specimens"] + "\n\n"
                        dlgRemoveSpecies.message += "This will delete all baskets and specimens that\n you've collected on this haul for this species"
                        dlgRemoveSpecies.action = "Are you sure that you want to do this?"
                        dlgRemoveSpecies.open()
                    } else {
                        removeSpecies()
                    }
                }
            }
        } // btnRemoveSpecies
        TrawlBackdeckButton {
            id: btnCreateMix
            text: qsTr("Create\nMix")
            onClicked: {
                var seModel = tvSelectedSpecies.model
                var index = tvSelectedSpecies.selModel.currentIndex
                var item = seModel.getItem(index)
                var typeRoleNum = processCatch.SelectedSpeciesModel.getRoleNumber("type")
                var type = tvSelectedSpecies.model.data(index, typeRoleNum)

                var label;
                var childType;
                if (type && type === "Mix") {
                    label = "Submix "
                    childType = "Submix";
                } else {
                    label = "Mix "
                    childType = "Mix"
                }

                var mixCount = tvSelectedSpecies.model.addMixCount(childType, index)

                var itemData = {"displayName": label + "#" + mixCount, "type": childType}
                processCatch.append_tree_item_with_sql(itemData, index, type)

                // Sort the Tree
                sortTreeView(index)

                // Check the current parent + parent index
                if ((type == "Mix") || (type == "Submix")) {
                    var parentItem = item;
                    var parent = index;
                } else {
                    var parentItem = seModel.rootItem;
                    var parent = null;
                }

                // Select the newly created mix or submix - this facilitates more rapid data entry by the user
                var newItem;
                var newIndex;
                var newRow;
                var displayNameRole = tvSelectedSpecies.model.getRoleNumber("displayName");
                if (childType === "Mix") {
                    newIndex = tvSelectedSpecies.model.get_index_by_role_value("displayName", itemData["displayName"]);
                    newRow = newIndex.row;
                } else if (childType === "Submix") {
                    newRow = parentItem.child(parentItem.childCount()-1).row
                }
                console.info("newIndex = " + newIndex);
                console.info('display = ' + itemData['displayName']);
                console.info('newRow = ' + newRow);
                console.info('mixCount = ' + mixCount + ', childType = ' + childType);

                var newIndex = seModel.index(newRow, 0, parent)
                tvSelectedSpecies.selModel.setCurrentIndex(newIndex, 0x0002 | 0x0010)

                // If the first mix is added, make it the activeMix
//                if ((mixCount === 1) && (childType === "Mix")) {
                var displayName = tvSelectedSpecies.model.data(newIndex, displayNameRole);
                var catchIdRole = tvSelectedSpecies.model.getRoleNumber("catchId");
                var catchId = tvSelectedSpecies.model.data(newIndex, catchIdRole);
                if ((displayName.indexOf("Mix") != -1) || (displayName.indexOf("Submix") != -1)) {
                    processCatch.activeMix = {"catchId": catchId, "displayName": displayName};
                }
//                }

                // Enable the Remove Button
                btnRemoveSpecies.state = qsTr("enabled")

            }
        } // btnCreateMix
        TrawlBackdeckButton {
            id: btnAddToMix
            text: qsTr("Add To\nMix")
//            state: qsTr("disabled")
            state: processCatch.activeMix["displayName"] ? qsTr("enabled") : qsTr("disabled")
            onClicked: { addSpecies(true) }
        } // btnAddToMix
        TrawlBackdeckButton {
            id: btnActiveMix
            text: processCatch.activeMix["displayName"] ? qsTr("Active Mix\n" + processCatch.activeMix["displayName"]) :
                qsTr("Active Mix\n")
            onClicked: {
                var index = tvSelectedSpecies.selModel.currentIndex;
                var displayNameRole = tvSelectedSpecies.model.getRoleNumber("displayName");
                var catchIdRole = tvSelectedSpecies.model.getRoleNumber("catchId");
                var displayName = tvSelectedSpecies.model.data(index, displayNameRole);
                var catchId = tvSelectedSpecies.model.data(index, catchIdRole);
                if ((displayName.indexOf("Mix") != -1) || (displayName.indexOf("Submix") != -1)) {
                    processCatch.activeMix = {"catchId": catchId, "displayName": displayName};
                }
            }
//            state:
        } // btnActiveMix
//        TrawlBackdeckButton {
//            id: btnSizeStrata
//            text: qsTr("Size\nStrata")
//            state: qsTr("disabled")
//        } // btnSizeStrata
//        TrawlBackdeckButton {
//            id: btnLifestageStrata
//            text: qsTr("Lifestage\nStrata")
//            state: qsTr("disabled")
//        } // btnLifestageStrata
    }

    GridLayout {
        id: gridProcessFishMetadata
        columns: 3
        x: colSpeciesControllers.x + colSpeciesControllers.width + 40
        y: 5
        columnSpacing: 20
        Label {
            id: lblHaulID
            text: qsTr("Haul ID")
            font.pixelSize: 18
        }
        Label {
            id: lblTotalWeight
            text: qsTr("Total Weight")
            font.pixelSize: 18
        }
        Label {
            id: lblTotalSpecies
            text: qsTr("Total Species")
            font.pixelSize: 18
        }
        TrawlBackdeckTextFieldDisabled {
            id: tfHaulId
            text: stateMachine.haul["haul_number"] // "423"
            font.pixelSize: 18
            readOnly: true
//            Layout.maximumWidth: 250
            Layout.preferredWidth: 160
        }
        TrawlBackdeckTextFieldDisabled {
            id: tfTotalWeight
            text: processCatch.totalWeight ? parseFloat(processCatch.totalWeight).toFixed(1) : ""
            font.pixelSize: 18
            readOnly: true
            Layout.maximumWidth: 100
        }
        TrawlBackdeckTextFieldDisabled {
            id: tfTotalSpecies
//            text: "7"
            text: processCatch.speciesCount
            font.pixelSize: 18
            readOnly: true
            Layout.maximumWidth: 100
        }
    } // gridProcessFishMetadata

    TrawlBackdeckTreeView {
        id: tvSelectedSpecies
        x: colSpeciesControllers.x + colSpeciesControllers.width + 40
        y: tvAvailableSpecies.y
        width: main.width - tvAvailableSpecies.width - colSpeciesControllers.width - 90
        height: tvAvailableSpecies.height
        selectionMode: SelectionMode.SingleSelection
        horizontalScrollBarPolicy: Qt.ScrollBarAlwaysOff

        property alias selModel: selModel

        model: processCatch.SelectedSpeciesModel

        selection: ItemSelectionModel {
            id: selModel
            model: tvSelectedSpecies.model
        }

        onClicked: {
            selModel.clearCurrentIndex();
            selModel.setCurrentIndex(index, 0x0002 | 0x0010);
        }

        onDoubleClicked: {
            // TODO Remove double-clicked species and add to the tvAvailableSpecies TableView
//            msg.show(currentIndex.row)
  //          msg.show(this.model.get(currentIndex.row).species)
//            tvAvailableSpecies.model.append({"species": this.model.get(currentIndex.row).species})
//            this.model.remove(currentIndex.row)
            selModel.clearCurrentIndex();
            selModel.setCurrentIndex(index, 0x0002 | 0x0010);

            var currentIndex = tvSelectedSpecies.selModel.currentIndex
            var typeRoleNum = processCatch.SelectedSpeciesModel.getRoleNumber("type")
            var type = tvSelectedSpecies.model.data(currentIndex, typeRoleNum)

            if ((!screens.busy) & (index.row >= 0) & (type != "Mix") & (type != "Submix")) {
//                screens.push(Qt.resolvedUrl("WeighBasketsScreen.qml"))
//                tbdSM.to_weigh_baskets_state()
            } else if ((type == "Mix") || (type == "Submix")) {
                if (tvSelectedSpecies.isExpanded(currentIndex)) {
                    tvSelectedSpecies.collapse(currentIndex)
                } else {
                    tvSelectedSpecies.expand(currentIndex)
                }
            }
        }

        TableViewColumn {
            role: "displayName"
            title: "Species"
            width: 250
            delegate: Text {
                text: styleData.value ? styleData.value.substring(0, Math.floor(this.width/9.3)) : ""
                width: 250
                font.pixelSize: 20
                verticalAlignment: Text.AlignVCenter
            }
        } // displayName
        TableViewColumn {
            role: "weight"
            title: "kg"
            width: 60
            delegate: Text {
                text: styleData.value ? styleData.value.toFixed(0) : ""
                font.pixelSize: 20
                verticalAlignment: Text.AlignVCenter
            }
        } // weight
        TableViewColumn {
            role: "count"
            title: "#"
            width: 50
            delegate: Text {
                text: styleData.value ? styleData.value.toFixed(0) : ""
                font.pixelSize: 20
                verticalAlignment: Text.AlignVCenter
            }
        } // count
        TableViewColumn {
            role: "protocol"
            title: "Protocol"
            delegate: Text {
                text: styleData.value ? styleData.value : ""
                font.pixelSize: 20
                verticalAlignment: Text.AlignVCenter
            }
        } // protocol
    } // tvSelectedSpecies

    RowLayout {
        x: main.width - this.width - 10
        y: main.height - this.height - 20
        spacing: 5

        TrawlBackdeckButton {
            id: btnWeighBaskets
            text: qsTr("Weigh\nBaskets")
            state: qsTr("disabled")
            Layout.preferredHeight: this.height
            Layout.preferredWidth: this.width
            onClicked: {
                if (!screens.busy)
                    screens.push(Qt.resolvedUrl("WeighBasketsScreen.qml"))
                    tbdSM.to_weigh_baskets_state()
            }
        } // btnWeighBaskets
        TrawlBackdeckButton {
            id: btnFishSampling
            text: qsTr("Fish\nSampling")
            state: qsTr("disabled")
            Layout.preferredHeight: this.height
            Layout.preferredWidth: this.width
//            onClicked: {
//                if (!screens.busy)
//                    screens.push(Qt.resolvedUrl("FishSamplingScreen.qml"))
//            }
        } // btnFishSampling
        TrawlBackdeckButton {
            id: btnSpecialAction
            text: qsTr("Special\nActions")
            state: qsTr("disabled")
            Layout.preferredHeight: this.height
            Layout.preferredWidth: this.width
            onClicked: {
                if (!screens.busy)
                    screens.push(Qt.resolvedUrl("SpecialActionsScreen.qml"))
                    tbdSM.to_special_actions_state()
            }
        } // btnSpecialAction
        TrawlBackdeckButton {
            id: btnValidateHaul
            text: qsTr("Val")
            Layout.preferredHeight: this.height
            Layout.preferredWidth: 60
            onClicked: { dlgValidate.open() }
        } // btnValidateHaul
        TrawlBackdeckButton {
            id: btnNotes
            text: qsTr("Note")
            Layout.preferredHeight: this.height
            Layout.preferredWidth: 60
            onClicked: {
                dlgNote.reset(tvSelectedSpecies)
                dlgNote.open()
            }
        } // btnNotes

        TrawlBackdeckButton {
            id: btnBack
            text: qsTr("<<")
//            width: 60
            Layout.preferredHeight: this.height
            Layout.preferredWidth: 60
            onClicked: screens.pop()
        } // btnBack
    }

    TrawlValidateDialog {
        id: dlgValidate
    }
    TrawlConfirmDialog {
        id: dlgRemoveSpecies
        height: 500
        message: "You are about to remove "
        action: "This will remove any baskets or specimens that have been collected"
        onAccepted: {
            removeSpecies();
        }
    }

    FramSlidingKeyboard {
        id: keyboard
        x: 650
        y: 500

        onButtonOk: {
            resetfocus()
//            tfSpecies.forceActiveFocus();
//            if (this.keyboard_result)
//                tfSpecies.text = this.keyboard_result
        }
    } // keyboard

    FramConfirmDialog {
        id: dlgConfirm
        visible: false
        action_label: "remove the species\nit has data associated with it"

        auto_hide: false
        auto_label: false

//        dlgConfirm.hide()

        onCancelledFunc: {
            this.hide()
        }

//        onConfirmed: {
//            columnAvailSpecies.removeSpecies();
//            visible = false;
//        }
        onConfirmedFunc: {
//            CommonUtil.debug("Confirmed " + action_name);
         //   columnAvailSpecies.removeSpecies();
//            visible = false;
           if (action_name == "no protocol") {
                loadSamplingScreen();
                this.hide();
           }

        }

    } // FramConfirmDialog

    TrawlNoteDialog { id: dlgNote }
    TrawlOkayDialog { id: dlgOkay }
}