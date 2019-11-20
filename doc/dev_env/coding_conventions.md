# Coding Conventions for OPTECS

_Unauthoritative rough draft. Needs completion, review, and consensus._

## Background

Implemented using Python and PyQt. PyQt's QML contains Javascript. This convention intends to cover the use of these two languages in these two separate contexts:

* Python in .py files.
* JavaScript in .qml files.

Conventions cover both languages unless [PY] or [JS] notation is shown.

## Braces for Functions and If-statements

* Opening brace on function definition or if statement, 
not on separate line.
    * JS Example:
    ```
    if (direct_connect || duplicate_connect) {
        if (connect_tf) {
            connect_tf.text = textNumPad.text;
            connect_tf.cursorPosition = textNumPad.cursorPosition;
        }
    }
    ```

## Line Length and Terminator

* Line length: 120 characters, 40 more than PEP-8 allows. Justification: Indentation can get deep in QML controls within controls.
    
* Line-Ending Style: development is taking place on Windows systems, so end lines with CR+LF.

_Question: I'm not sure what we store our source with. GitHub typically stores with LF terminator and Windows users use ```git config core.autocrlf true```. What does NOAA GitLab do?_

## Tabs, Spaces, Indentation and End-of-Line

* Store tabs as four spaces.
* Indentation is four spaces.
* One indent typical. Exception: two indents for continuation lines of a statement or function definition. JS Example:
     ```
     if (!appstate.trips.TripCertsModel.is_item_in_model(
             "certificate_number", textNewCert.text)) {
         appstate.trips.addTripCert(textNewCert.text);
     } else {
         ...
     ```

## Continuation Lines

If a statement must continue over multiple lines,
continuation lines should be doubly-indented.
Try to end a line with an operator (rather than starting new line with operator).

PY Example:
```
catch_category_q = Catches.select(). \
        where(Catches.fishing_activity == fishing_activity_id). \
        order_by(Catches.catch_num)
```
JS Example:
```
message: "Depth of " + invalidDepth +
        " exceeds " + trawl_max_depth_fathoms + " fathoms.\n" +
        "Please ensure fishing depth,\n" + 
        "not bottom depth, is recorded." 
```
(Note double indentation for continuation)
    
## Naming Conventions

### Python Classes, Properties, and Methods

* Underscores: _"Use one leading underscore only for non-public methods and instance variables."_ [PEP-8]

* Double underscores: _"To avoid name clashes with subclasses, use two leading underscores to invoke Python's name mangling rules."_ [PEP-8]

### @pyqtSlot

@pyqtSlot is a decoration on a Python method - a python method intended to be called
by QML JavaScript. Python methods use lowercase separated by underscores;
JavaScript uses lower camelCase. pyqtSlots bridge the two. Which convention to use?

Proposed: __Honor both - using @pyqtSlot's _name_ parameter.__

@pyqtSlot has a _name_ parameter. Use that to specify how the JavaScript caller
will know the method, and use a Pythonic method name in the def statement.

Example:
```
    @pyqtSlot(QVariant, name='setActiveListModel')
    def set_active_list_model(self, model_type):
```

### @pyqtProperty

@pyqtProperty is another decoration on a python method intended to be called
by QML JavaScript. Python methods use lowercase separated by underscores;
JavaScript uses lower camelCase. pyqtProperty bridges the two,
but it doesn't have a _name_ parameter (at least of 5.7).
Which convention to use?

Proposed: __Honor the caller's convention (JavaScript lower camelCase).__

Rationale: it's close to a coin toss. Give the nod to JavaScript in order to 
reinforce the @pyqtProperty attribute: this method is intended for use in foreign territory.
Use lower CamelCase:

```
    @pyqtProperty(QVariant, notify=modelChanged)
    def catchCategorySelectedModel(self):
```
### Events and Event Handlers

(Chat discussion between Will Smith and Jim Stearns, 28-Oct-2016):
```
Will, I'm working on Eric's field advance in GPS Entry. I"m mostly there, but I'm running into a corner case: what if the user wants to skip to the next field by entering "00" in say, minutes.
I'm running into FramScalingNumPad's behavior of parsing out leading zeros.
Will Smith - NOAA Affiliate (will.smith@noaa.gov)
ahh yes
I suppose adding a "multi-zero" property to allow that would be in order
Great - I was hoping you'd say that. I'll do that. 
Will Smith - NOAA Affiliate (will.smith@noaa.gov)
Cool. Interesting things abound when we write our own ultra-custom inputs
How about "leading_zero_mode" for property name (default false)?
Will Smith - NOAA Affiliate (will.smith@noaa.gov)
I think the pyQt case would be leadingZeroMode (e.g.  we'll get onLeadingZeroModeChanged )
I haven't been as consistent as I should though, so whatever you think matches 
Ah, good point. I'll go with leadingZeroMode.
It's a little jarring to see the mix of adding_mode and decimalKeyMode, but there's a decent rationale behind the two formats ...
python_underscore for internal properties, camelCase for properties that may be set from outside via events?
I'm probably missing something, but I don't think a signal handler is needed here. leading_zero_mode is a property read at instantiation and will not change - I don't see a use case for switching this mode during operation.
If that's the case - a variable read at instantation, essentially a const variable - can't the property be defined, with the including call specifying the property value as in:
FramScalingPad {
   id: whatever
  leading_zero_mode: true
...
Will Smith - NOAA Affiliate (will.smith@noaa.gov)
sure
there will, automatically, be a onLeading_zero_modeChanged, but we won't use it
So perhaps that's the rule: use camelCase variable naming if an explicit handler is created, python_case otherwise?
Will Smith - NOAA Affiliate (will.smith@noaa.gov)
as a side note, I noticed a PEP-8 compliant way to make both python and PyQt happy
@pyQtProperty(name='examplePropName')
def example_prop_name(self):
so, pyqt will see the name it likes, and pep-8 linting will also be pleased
I haven't actually done that though, because it seems easy to forget to change the name arg
in fact name arg is optional, so just leaving it off probably makes the most sense
although pycharm complains
Will • 52 mins
Oh, I like that @pyQtProperty(name=''"), where name would be the name as seen by JavaScript, yes? That would be the best of both worlds, where the python interface code documents the variable name mapping.
Will Smith - NOAA Affiliate (will.smith@noaa.gov)
yes
But I can't find documentation for that name parameter. Is it new? I'm looking at http://pyqt.sourceforge.net/Docs/PyQt5/qt_properties.html#defining-new-qt-properties
Will Smith - NOAA Affiliate (will.smith@noaa.gov)
I don't recall how I came across it
super duper secret code
I haven't actually played with it much--it may not actually work the way I envision
very odd that it's not even mentioned in the docs
You should have defined the API ☺
Will Smith - NOAA Affiliate (will.smith@noaa.gov)
oh, well it appears I was mistaken, thinking of pyqtSlot
one day I dream of a name field in pyqtProperty...
indeed, http://pyqt.sourceforge.net/Docs/PyQt5/signals_slots.html#the-pyqtslot-decorator
```

# Project and Application Assumptions

* Intended for English readers. No internationalization plans.
    * Any qsTr("text") are no longer required and can be removed.
* Latitudes and Longitudes are for Northwest quadrasphere, the intersection of the Northern and Western Hemispheres that include U.S. coastal waters. In other words, a positive sign for the latitude and negative for the longitude is often presented in the label of a text field.
