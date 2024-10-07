Engage Quickstart
======================

Overview
--------------
After creating an Engage account, building and running models in Engage consists of:
1. creating a model from scratch or copying a model on which to base the new model, then, after entering the model, in the new model (this is done on the Models page)...
2. creating locations at which existing (baseline) and expansion technologies will be placed (this is done on the Locations tab)
3. populating the technology catalog in the model with technologies that will represent existing and expansion technologies when they are placed at locations in the model (this is done on the Technologies tab)
4. creating "nodes" by placing technologies on locations in the model and, as needed, interconnecting locations with transmission (this is done on the Nodes tab)
5. creating scenarios and then defining the scenarios by configuring settings specific to each scenario and turning on or activating the nodes that the scenario utilizes
6. running scenarios, troubleshooting the runs, evaluating results of the runs, and iterating the model configurations until the model run answers the question the scenario was designed to answer
The following sections provide brief overviews of each.

Locations
--------------
Locations correspond to real-world places where technologies in a model are positioned. They are are created on the Locations tab.
![[Pasted image 20240928194532.png]]
New locations can be created by clicking on the green "+New" button in the upper right corner of the Locations tab. Clicking the button creates a new location in the center of the map, creates a row below the map corresponding to the new location, and places the cursor in the New Location Name field on that row, allowing the modeler to give the new location a name. After the location information is populated, the modeler hits the "Save" button on the far right side of the row to save the location information.
The location indicators on the map on this tab can be dragged and dropped to update their physical location on the map. When this is done, the location of interest is returned to edit mode with its row scrolled to the top of the list, and the Save button must again be used to persist the new physical location associated with the edited location.

Technologies
--------------
Technologies are the elements of a model that usually cost money to build and operate, and have certain operating characteristics related to cost, emissions, etc. Technologies are created by the modeler and become available in the Technologies catalog of the model. A technology can be placed into the model as many times as it is needed, so a technology that exists in the Technology Catalog can appear multiple times in the model, with the limitation that a given technology can only appear once at any given location. Technologies represent the *classes of devices* (as opposed to *instances of devices*) that the model simulates operation of and determines the optimal capacities of. Instances of technologies are created in the model after the technologies are populated into the Technologies Catalog by placing them at Locations to create Nodes in the next step, on the Nodes tab. 
The technologies catalog can be populated on the Technologies tab. The default view of the Technologies tab is to display a selected technology from the catalog, its definition in the Technology Definition frame, a diagram of its technology archetype in the Technology Archetype frame, and the currently configured parameters and constraints in the parameters list below.
![[Pasted image 20240928195042.png]]
The listed and selectable contents of the catalog can be seen by clicking in the large grey dropdown selector that spans the browser window under the workflow tabs. 
![[Pasted image 20240928195148.png]]
A new technology can be added to the catalog by clicking on the "+New" button in the upper right corner of the screen. Clicking this button takes the user to the New Technologies Page.
![[Pasted image 20240928195701.png]]
On the New Technologies Page, a new technology can be created by doing two things
* typing a name for the new technology in the large yellow "Name of new technology..." field that spans the browser window under the workflow tabs, and 
* selecting a technology archetype on which to base the new technology catalog entry from the table below by scrolling down the page, navigating to the archetype of interest, and either clicking on a box to build the technology from scratch (based on an archetype with all default configuration), clicking on a box to "Build from existing" (to base the technology on a technology that is already in the catalog of the current model), or by clicking on a box to "Build from publicly available" to base the technology on one of the preconfigured example technologies available in Engage.
These two actions can be performed in any order.
After the technology on which to base the new technology has been selected and a name provided, the yellow "Save" button will appear in the upper right of the screen and must be clicked to bring the new technology into the catalog. The modeler is then returned to the Technologies tab where the new technology is displayed. If the technology is being configured from scratch, it will not have a (required) carrier associated with it, and the carrier selector in the Technology Definition frame will be highlighted in red. The new technology cannot be saved at least until carriers are selected.
From here on the Technologies tab, the technology in the catalog can be configured by setting parameter and constraint values in the parameters list below the Technology Definition and Diagram frames.
There is more information about specific parameter configurations in the rest of this manual and in the Calliope documentation.
 
Nodes
--------------
Technologies are the elements of a model that usually cost money to build and operate, and have certain operating characteristics related to cost, emissions, etc. Technologies are created by the modeler and become available in the Technologies catalog of the model. A technology can be placed into the model as many times as it is needed, so a technology that exists in the Technology Catalog can appear multiple times in the model, with the limitation that a given technology can only appear once at any given location. Technologies represent the *classes of devices* (as opposed to *instances of devices*) that the model simulates operation of and determines the optimal capacities of. Instances of technologies are created in the model after the technologies are populated into the Technologies Catalog by placing them at Locations to create Nodes in the next step, on the Nodes tab. 
The technologies catalog can be populated on the Technologies tab. The default view of the Technologies tab is to display a selected technology from the catalog, its definition in the Technology Definition frame, a diagram of its technology archetype in the Technology Archetype frame, and the currently configured parameters and constraints in the parameters list below.
![[Pasted image 20240928195042.png]]
The listed and selectable contents of the catalog can be seen by clicking in the large grey dropdown selector that spans the browser window under the workflow tabs. 
![[Pasted image 20240928195148.png]]
A new technology can be added to the catalog by clicking on the "+New" button in the upper right corner of the screen. Clicking this button takes the user to the New Technologies Page.
![[Pasted image 20240928195701.png]]
On the New Technologies Page, a new technology can be created by doing two things
* typing a name for the new technology in the large yellow "Name of new technology..." field that spans the browser window under the workflow tabs, and 
* selecting a technology archetype on which to base the new technology catalog entry from the table below by scrolling down the page, navigating to the archetype of interest, and either clicking on a box to build the technology from scratch (based on an archetype with all default configuration), clicking on a box to "Build from existing" (to base the technology on a technology that is already in the catalog of the current model), or by clicking on a box to "Build from publicly available" to base the technology on one of the preconfigured example technologies available in Engage.
These two actions can be performed in any order.
After the technology on which to base the new technology has been selected and a name provided, the yellow "Save" button will appear in the upper right of the screen and must be clicked to bring the new technology into the catalog. The modeler is then returned to the Technologies tab where the new technology is displayed. If the technology is being configured from scratch, it will not have a (required) carrier associated with it, and the carrier selector in the Technology Definition frame will be highlighted in red. The new technology cannot be saved at least until carriers are selected.
From here on the Technologies tab, the technology in the catalog can be configured by setting parameter and constraint values in the parameters list below the Technology Definition and Diagram frames.
There is more information about specific parameter configurations in the rest of this manual and in the Calliope documentation.
 
Scenarios
--------------
text

Runs
--------------
text