import QtQuick 2.2

ListModel {
    ListElement {
        stage: "Adult"
        population: "Wild"
        condition: "Alive"
        count: 1
    }
    ListElement {
        stage: "Adult"
        population: "Wild"
        condition: "Dead"
        count: 1
    }
    ListElement {
        stage: "Adult"
        population: "Hatchery"
        condition: "Alive"
        count: 1
    }
    ListElement {
        stage: "Adult"
        population: "Hatchery"
        condition: "Dead"
        count: 0
    }
    ListElement {
        stage: "Sub-Adult"
        population: "Wild"
        condition: "Alive"
        count: 1
    }
    ListElement {
        stage: "Sub-Adult"
        population: "Wild"
        condition: "Dead"
        count: 1
    }
    ListElement {
        stage: "Sub-Adult"
        population: "Hatchery"
        condition: "Alive"
        count: 1
    }
    ListElement {
        stage: "Sub-Adult"
        population: "Hatchery"
        condition: "Dead"
        count: 0
    }    
}