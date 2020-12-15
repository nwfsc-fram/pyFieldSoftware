// Covers the 4 primary data entry views: Catch Categories, Species, Weights, Biospecimens
import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

import "."
import "../common"

FramTabView {
    id: tabView

    function page_state_id() { // for transitions
        return "tabs_screen";
    }

    property alias tabCC: tabCC
    property alias tabSp: tabSp
    property alias tabCW: tabCW
    property alias tabBS: tabBS

    property var pageCC: null // set when page onCompleted
    property var pageSpecies: null  // set when page onCompleted
    property var pageCW: null  // set when page onCompleted
    property var pageBS: null  // set when page onCompleted

    signal selectedCatchCatChanged()
    signal selectedSpeciesChanged()

    signal enableEntryTabs(bool enable)
    onEnableEntryTabs: {
        tabSp.enabled = enable
        tabCW.enabled = enable
        tabBS.enabled = enable
    }

    signal enableCatchCategoriesTab(bool enable)
    onEnableCatchCategoriesTab: {
        // console.debug(enable ? "Enabled" : "Disabled");
        tabCC.enabled = enable
    }

    signal enableSpeciesTab(bool enable)
    onEnableSpeciesTab: {
        tabSp.enabled = enable
    }

    signal enableCountWeightTab(bool enable)
    onEnableCountWeightTab: {
        // console.debug(enable ? "Enabled" : "Disabled");
        tabCW.enabled = enable
    }


    function allow_enable_biospecimens_tab() {
        // Enable entry into Biospecimens screen if the Catch Category has a current species
        // and either:
        // (1) its Disposition is Retained, or
        // (2) its Disposition is Discarded and a discard reason has been specified,
        //      at the relevant level of catch category (NSC) or the species (SC).
        var isSC = appstate.catches.currentSampleMethodIsSpeciesComposition;
        var current_species_id = appstate.catches.species.currentSpeciesItemCode;
        if (current_species_id === undefined && isSC) {
            console.debug("Tab disabled - no species and is Species Comp");
            return false;
        }
        if (current_species_id === undefined && !appstate.catches.isSingleSpecies) {
            console.debug("Tab disabled - not a single species");
            return false;
        }

        var catch_category_disposition = appstate.catches.getData('catch_disposition');
        if (catch_category_disposition == 'R') {
            console.debug("Enabled - CC has species and Retained Disposition.");
            return true;
        } else {    // Disposition = 'D' (Discarded)

            var discardReason = isSC ?
                    appstate.catches.species.discardReason :
                    appstate.catches.getData('discard_reason');

            if (discardReason != null) {
                console.debug("Enabled - " + (isSC ? "Species" : "Catch") +
                        " discard reason = " + discardReason + ".");
                return true;
            } else {
                console.debug("Disabled - " + (isSC ? "Species" : "Catch") +
                        " discard reason is null.");
                return false;
            }
        }
    }

    signal enableBiospecimensTab(bool enable)
    onEnableBiospecimensTab: {
        if (enable) {
            enable = allow_enable_biospecimens_tab();
        }
        console.debug(enable ? "BIOS Enabled" : "BIOS Disabled");
        tabBS.enabled = enable
    }

    Component.onCompleted: {
        obsSM.state_change("cc_entry_state");
        enableEntryTabs(false);
    }

    Connections {
        target: framHeader
        onJumpFromCCSubsidiaryScreenToTab: {
            if (!appstate.catches.currentSampleMethodIsNoSpeciesComposition) {
                tabView.currentIndex = 1; // Species
            } else {
                tabView.currentIndex = 3; // Biospecimens
            }
        }
        onRevertToCW: {  // FIELD-2039: signal to go back to CW tab
            tabView.currentIndex = 2
        }
    }

    onCurrentIndexChanged: {
        switch(currentIndex) {
        case 0:
            obsSM.state_change("cc_entry_state");
            break;
        case 1:
            obsSM.state_change("species_entry_state");
            break;
        case 2:
            obsSM.state_change("cw_entry_state");
            break;
        case 3:
            obsSM.state_change("bs_entry_state");
            break;

        }
    }

    Tab {
        id: tabCC
        title: "Catch Categories"
        active: true  // Load tab at runtime
        CatchCategoriesScreen {
            Component.onCompleted: {
                pageCC = this;
            }
        }
    }
    Tab {
        id: tabSp
        title: "Species"
        active: true  // Load tab at runtime
        SpeciesScreen {
            Component.onCompleted: {
                pageSpecies = this;
            }
        }
    }
    Tab {
        id: tabCW
        title: "Counts/Weights"
        active: true  // Load tab at runtime
        CountsWeightsScreen {
            Component.onCompleted: {
                pageCW = this;
            }
        }
    }
    Tab {
        id: tabBS
        title: "Biospecimens"
        active: true  // Load tab at runtime
        BiospecimensScreen {
            Component.onCompleted: {
                pageBS = this;
            }
        }
    }
}
