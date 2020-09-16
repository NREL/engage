

function autocomplete_units(inp) {
  /*the autocomplete function takes two arguments,
  the text field element and an array of possible autocompleted values:*/
  var currentFocus,
      arr = [];
  user_defined_units.forEach(function(d) { arr.push(d['name']) })
  /*execute a function when someone writes in the text field:*/
  inp.addEventListener("input", function(e) {
      var a, b, i,
          val = this.value.split(' ');
      val = val[val.length - 1]
      /*close any already open lists of autocompleted values*/
      closeAllLists();
      // if (!val) { return false;}
      currentFocus = -1;
      /*create a DIV element that will contain the items (values):*/
      a = document.createElement("DIV");
      a.setAttribute("id", this.id + "autocomplete-list");
      a.setAttribute("class", "autocomplete-items");
      /*append the DIV element as a child of the autocomplete container:*/
      this.parentNode.appendChild(a);
      /*for each item in the array...*/
      for (i = 0; i < arr.length; i++) {
        /*check if the item starts with the same letters as the text field value:*/
        if (arr[i].toUpperCase().includes(val.toUpperCase())) {
          /*create a DIV element for each matching element:*/
          b = document.createElement("DIV");
          /*make the matching letters bold:*/
          var start_index = arr[i].toUpperCase().split(val.toUpperCase())[0].length,
              end_index = start_index + val.length;
          b.innerHTML = arr[i].substring(0, start_index)
          if (start_index != end_index) { b.innerHTML += "<strong style='background-color: #ffff0040;border: solid 1px silver;'>" + arr[i].substring(start_index, end_index) + "</strong>"; };
          b.innerHTML += arr[i].substring(end_index);
          /*insert a input field that will hold the current array item's value:*/
          b.innerHTML += "<input type='hidden' value='" + arr[i] + "'>";
          /*execute a function when someone clicks on the item value (DIV element):*/
              b.addEventListener("click", function(e) {
              /*insert the value for the autocomplete text field:*/
              var old_value = inp.value,
                  new_value = this.getElementsByTagName("input")[0].value;
              old_value = old_value.substr(0, old_value.length - val.length);
              inp.value = old_value + new_value;
              if (!$(inp).is(":focus")) {
                // Refocus
                $(inp).focus();
                var tmpStr = $(inp).val();
                $(inp).val(''); $(inp).val(tmpStr);
              }
              $(inp).change();
              /*close the list of autocompleted values,
              (or any other open lists of autocompleted values:*/
              closeAllLists();
          });
          a.appendChild(b);
        }
      }
  });
  /*execute a function presses a key on the keyboard:*/
  inp.addEventListener("keydown", function(e) {
    var x = document.getElementById(this.id + "autocomplete-list");
    if (x) x = x.getElementsByTagName("div");
    if (e.keyCode == 40) {
      /*If the arrow DOWN key is pressed,
      increase the currentFocus variable:*/
      currentFocus++;
      /*and and make the current item more visible:*/
      addActive(x);
    } else if (e.keyCode == 38) { //up
      /*If the arrow UP key is pressed,
      decrease the currentFocus variable:*/
      currentFocus--;
      /*and and make the current item more visible:*/
      addActive(x);
    } else if (e.keyCode == 13) {
      setTimeout(function() {
        if (currentFocus > -1) { /*and simulate a click on the "active" item:*/
          if (x) x[currentFocus].click();
        } else {
          closeAllLists();
        };
      }, 100);
    } else if (e.keyCode == 9) {
      closeAllLists();
    };
  });
  function addActive(x) {
    /*a function to classify an item as "active":*/
    if (!x) return false;
    /*start by removing the "active" class on all items:*/
    removeActive(x);
    if (currentFocus >= x.length) currentFocus = 0;
    if (currentFocus < 0) currentFocus = (x.length - 1);
    /*add class "autocomplete-active":*/
    x[currentFocus].classList.add("autocomplete-active");
  }
  function removeActive(x) {
    /*a function to remove the "active" class from all autocomplete items:*/
    for (var i = 0; i < x.length; i++) {
      x[i].classList.remove("autocomplete-active");
    }
  }
  function closeAllLists(elmnt) {
    /*close all autocomplete lists in the document,
    except the one passed as an argument:*/
    var x = document.getElementsByClassName("autocomplete-items");
    for (var i = 0; i < x.length; i++) {
      if (elmnt != x[i] && elmnt != inp) {
        x[i].parentNode.removeChild(x[i]);
      }
    }
  }
  /*execute a function when someone clicks in the document:*/
  document.addEventListener("click", function (e) {
      closeAllLists(e.target);
  });
}




function initiate_units() {

	math.createUnit('percent', {definition: '1', aliases: ['percent', 'percentage'], baseName: 'percent'});
	math.createUnit('dpercent', {definition: '100 percent', aliases: ['dpercent', 'dpercentage']});
	math.createUnit('dollar', {definition: '1', aliases: ['dollar', 'dollars'], baseName: 'dollar'});
	math.createUnit('cent', {definition: '0.01 dollar', aliases: ['c', 'cent', 'cents']});

	user_defined_units.forEach(function(item) {
		var pretty_name = item['name'],
			name = item['name'].split('[')[0].replaceAll('_', ''),
			val = item['value'];
		math.createUnit(name, {definition: val, baseName: name});
	})

}

function convert_units(old_units, new_units, strict) {

	old_units = _clean_units(old_units);
	new_units = _clean_units(new_units);
	try {
	  	var val = math.evaluate(old_units);
	  	if (val.isUnit == undefined) {
	  		return val;
	  	} else {
	 		return val.toNumber(new_units);
	 	}
	}
	catch(err) {
		if (strict != true) {
			result = convert_units(old_units.toLowerCase(), new_units, true);
			if (result != false) { return result };
			result = convert_units(old_units.toUpperCase(), new_units, true);
			return result;
		} else {
			return false;
		};
	}

}

function _clean_units(units) {
	units = String(units);
	units = units.replaceAll('$', 'dollar');
	units = units.replaceAll(',', '');
	units = units.replaceAll('%<sub>/100</sub>', 'dpercent').replaceAll('%', 'percent');
	units = units.replaceAll('<sup>2</sup>', '^2');
	user_defined_units.forEach(function(item) {
		var pretty_name = item['name'],
			name = item['name'].split('[')[0].replaceAll('_', '');
		units = units.replaceAll(pretty_name, name);
	})
	return units;
}

var user_defined_units = [
  {
    "name": "Crude_Oil_Low_Volume_Energy[28MJ/L]",
    "value": "28 MJ/L"
  },
  {
    "name": "Crude_Oil_High_Volume_Energy[31.4MJ/L]",
    "value": "31.4 MJ/L"
  },
  {
    "name": "Dried_Plants_Low_Volume_Energy[1.6MJ/L]",
    "value": "1.6 MJ/L"
  },
  {
    "name": "Dried_Plants_High_Volume_Energy[16.64MJ/L]",
    "value": "16.64 MJ/L"
  },
  {
    "name": "Wood_Fuel_Low_Volume_Energy[2.56MJ/L]",
    "value": "2.56 MJ/L"
  },
  {
    "name": "Wood_Fuel_High_Volume_Energy[21.84MJ/L]",
    "value": "21.84 MJ/L"
  },
  {
    "name": "Pyrolysis_Oil_Volume_Energy[21.35MJ/L]",
    "value": "21.35 MJ/L"
  },
  {
    "name": "Methanol_Mass_Energy[15.9MJ/L]",
    "value": "15.9 MJ/L"
  },
  {
    "name": "Ethanol_Low_Volume_Energy[18.4MJ/L]",
    "value": "18.4 MJ/L"
  },
  {
    "name": "Ethanol_High_Volume_Energy[21.2MJ/L]",
    "value": "21.2 MJ/L"
  },
  {
    "name": "Ecalene_Volume_Energy[22.7MJ/L]",
    "value": "22.7 MJ/L"
  },
  {
    "name": "Butanol_Volume_Energy[29.2MJ/L]",
    "value": "29.2 MJ/L"
  },
  {
    "name": "Fat_Volume_Energy[31.68MJ/L]",
    "value": "31.68 MJ/L"
  },
  {
    "name": "Biodiesel_Low_Volume_Energy[33.3MJ/L]",
    "value": "33.3 MJ/L"
  },
  {
    "name": "Biodiesel_High_Volume_Energy[35.7MJ/L]",
    "value": "35.7 MJ/L"
  },
  {
    "name": "Sunflower_Oil_Volume_Energy[33.18MJ/L]",
    "value": "33.18 MJ/L"
  },
  {
    "name": "Castor_Oil_Volume_Energy[33.21MJ/kg]",
    "value": "33.21 MJ/kg"
  },
  {
    "name": "Olive_Oil_Low_Volume_Energy[33.00MJ/L]",
    "value": "33.00 MJ/L"
  },
  {
    "name": "Olive_Oil_High_Volume_Energy[33.48MJ/L]",
    "value": "33.48 MJ/L"
  },
  {
    "name": "Methane_Liquified_Low_Volume_Energy[23.00MJ/L]",
    "value": "23.00 MJ/L"
  },
  {
    "name": "Methane_Liquified_High_Volume_Energy[23.3MJ/L]",
    "value": "23.3 MJ/L"
  },
  {
    "name": "Hydrogen__Liquified_Low_Volume_Energy[8.5MJ/L]",
    "value": "8.5 MJ/L"
  },
  {
    "name": "Hydrogen_Liquified_High_Volume_Energy[10.1MJ/L]",
    "value": "10.1 MJ/L"
  },
  {
    "name": "Coal_Low_Volume_Energy[39.85MJ/L]",
    "value": "39.85 MJ/L"
  },
  {
    "name": "Coal_High_Volume_Energy[74.43MJ/L]",
    "value": "74.43 MJ/L"
  },
  {
    "name": "Gasoline_Low_Volume_Energy[32MJ/L]",
    "value": "32 MJ/L"
  },
  {
    "name": "Gasoline_High_Volume_Energy[34.8MJ/L]",
    "value": "34.8 MJ/L"
  },
  {
    "name": "Diesel_Volume_Energy[40.3MJ/L]",
    "value": "40.3 MJ/L"
  },
  {
    "name": "Natural_Gas_Liquified_Low_Volume_Energy[25.5MJ/L]",
    "value": "25.5 MJ/L"
  },
  {
    "name": "Natural_Gas_Liquified_High_Volume_Energy[28.7MJ/L]",
    "value": "28.7 MJ/L"
  },
  {
    "name": "Ethane_Liquified_Volume_Energy[24MJ/L]",
    "value": "24 MJ/L"
  },
  {
    "name": "Propane_Lpg_Volume_Energy[91330BTU/gal]",
    "value": "91330 BTU/gal"
  },
  {
    "name": "Propane_Gas_60_Deg_Volume_Energy[2550/ft^3]",
    "value": "2550/ft^3"
  },
  {
    "name": "Butane_Volume_Energy[3200BTU/ft^3]",
    "value": "3200 BTU/ft^3"
  },
  {
    "name": "Fuel_Oil_No_1_Volume_Energy[137400BTU/gal]",
    "value": "137400 BTU/gal"
  },
  {
    "name": "Fuel_Oil_No_2_Volume_Energy[139600BTU/gal]",
    "value": "139600 BTU/gal"
  },
  {
    "name": "Fuel_Oil_No_3_Volume_Energy[141800BTU/gal]",
    "value": "141800 BTU/gal"
  },
  {
    "name": "Fuel_Oil_No_4_Volume_Energy[145100BTU/gal]",
    "value": "145100 BTU/gal"
  },
  {
    "name": "Fuel_Oil_No_5_Volume_Energy[148800BTU/gal]",
    "value": "148800 BTU/gal"
  },
  {
    "name": "Fuel_Oil_No_6_Volume_Energy[152400BTU/gal]",
    "value": "152400 BTU/gal"
  },
  {
    "name": "Heating_Oil_Volume_Energy[139000BTU/gal]",
    "value": "139000 BTU/gal"
  },
  {
    "name": "Kerosene_Volume_Energy[135000BTU/gal]",
    "value": "135000 BTU/gal"
  },
  {
    "name": "Residual_Fuel_Oil_Volume_Energy[6287000BTU/oilbarrel]",
    "value": "6287000 BTU/oilbarrel"
  },
  {
    "name": "Bagasse_Cane_Stalk_Mass_Energy[9.6MJ/kg]",
    "value": "9.6 MJ/kg"
  },
  {
    "name": "Chaff_Seed_Casings_Mass_Energy[14.6MJ/kg]",
    "value": "14.6 MJ/kg"
  },
  {
    "name": "Animal_Dung_Manure_Low_Mass_Energy[10MJ/kg]",
    "value": "10 MJ/kg"
  },
  {
    "name": "Animal_Dung_Manure_High_Mass_Energy[15MJ/kg]",
    "value": "15 MJ/kg"
  },
  {
    "name": "Dried_Plants_Low_Mass_Energy[10MJ/kg]",
    "value": "10 MJ/kg"
  },
  {
    "name": "Dried_Plants_High_Mass_Energy[16MJ/kg]",
    "value": "16 MJ/kg"
  },
  {
    "name": "Wood_Fuel_Low_Mass_Energy[16MJ/kg]",
    "value": "16 MJ/kg"
  },
  {
    "name": "Wood_Fuel_High_Mass_Energy[21MJ/kg]",
    "value": "21 MJ/kg"
  },
  {
    "name": "Charcoal_Mass_Energy[30MJ/kg]",
    "value": "30 MJ/kg"
  },
  {
    "name": "Dry_Cow_Dung_Mass_Energy[15MJ/kg]",
    "value": "15 MJ/kg"
  },
  {
    "name": "Dry_Wood_Mass_Energy[19MJ/kg]",
    "value": "19 MJ/kg"
  },
  {
    "name": "Pyrolysis_Oil_Mass_Energy[17.5MJ/kg]",
    "value": "17.5 MJ/kg"
  },
  {
    "name": "Methanol_Low_Mass_Energy[19.9MJ/kg]",
    "value": "19.9 MJ/kg"
  },
  {
    "name": "Methanol_High_Mass_Energy[22.7MJ/kg]",
    "value": "22.7 MJ/kg"
  },
  {
    "name": "Ethanol_Low_Mass_Energy[23.4MJ/kg]",
    "value": "23.4 MJ/kg"
  },
  {
    "name": "Ethanol_High_Mass_Energy[26.8MJ/kg]",
    "value": "26.8 MJ/kg"
  },
  {
    "name": "Ecalene_Mass_Energy[28.4MJ/kg]",
    "value": "28.4 MJ/kg"
  },
  {
    "name": "Butanol_Mass_Energy[36MJ/kg]",
    "value": "36 MJ/kg"
  },
  {
    "name": "Fat_Mass_Energy[37.656MJ/kg]",
    "value": "37.656 MJ/kg"
  },
  {
    "name": "Biodiesel_Mass_Energy[37.8MJ/kg]",
    "value": "37.8 MJ/kg"
  },
  {
    "name": "Sunflower_Oil_Mass_Energy[39.49MJ/kg]",
    "value": "39.49 MJ/kg"
  },
  {
    "name": "Castor_Oil_Mass_Energy[39.5MJ/kg]",
    "value": "39.5 MJ/kg"
  },
  {
    "name": "Olive_Oil_Low_Mass_Energy[39.25MJ/kg]",
    "value": "39.25 MJ/kg"
  },
  {
    "name": "Olive_Oil_High_Mass_Energy[39.82MJ/kg]",
    "value": "39.82 MJ/kg"
  },
  {
    "name": "Methane_Low_Mass_Energy[55.00MJ/kg]",
    "value": "55.00 MJ/kg"
  },
  {
    "name": "Methane_High_Mass_Energy[55.7MJ/kg]",
    "value": "55.7 MJ/kg"
  },
  {
    "name": "Hydrogen_Low_Mass_Energy[120MJ/kg]",
    "value": "120 MJ/kg"
  },
  {
    "name": "Hydrogen_High_Mass_Energy[142MJ/kg]",
    "value": "142 MJ/kg"
  },
  {
    "name": "Coal_Low_Mass_Energy[29.3MJ/kg]",
    "value": "29.3 MJ/kg"
  },
  {
    "name": "Coal_High_Mass_Energy[33.5MJ/kg]",
    "value": "33.5 MJ/kg"
  },
  {
    "name": "Crude_Oil_Mass_Energy[41.868MJ/kg]",
    "value": "41.868 MJ/kg"
  },
  {
    "name": "Gasoline_Low_Mass_Energy[45MJ/kg]",
    "value": "45 MJ/kg"
  },
  {
    "name": "Gasoline_High_Mass_Energy[48.3MJ/kg]",
    "value": "48.3 MJ/kg"
  },
  {
    "name": "Diesel_Mass_Energy[48.1MJ/kg]",
    "value": "48.1 MJ/kg"
  },
  {
    "name": "Natural_Gas_Low_Mass_Energy[38MJ/kg]",
    "value": "38 MJ/kg"
  },
  {
    "name": "Natural_Gas_High_Mass_Energy[50MJ/kg]",
    "value": "50 MJ/kg"
  },
  {
    "name": "Ethane_Mass_Energy[51.9MJ/kg]",
    "value": "51.9 MJ/kg"
  },
  {
    "name": "Household_Waste_Mass_Energy[9.5MJ/kg]",
    "value": "9.5 MJ/kg"
  },
  {
    "name": "Plastic_Mass_Energy[30MJ/kg]",
    "value": "30 MJ/kg"
  },
  {
    "name": "Car_Tires_Mass_Energy[35MJ/kg]",
    "value": "35 MJ/kg"
  },
  {
    "name": "Oil_Mass_Energy[2.4e7J/lbm]",
    "value": "2.4e7 J/lbm"
  }
]
