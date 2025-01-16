$(document).ready(function () {
  const tooltipTriggerList = document.querySelectorAll(
    '[data-bs-toggle="tooltip"]'
  );
  const tooltipList = [...tooltipTriggerList].map(
    (tooltipTriggerEl) => new bootstrap.Tooltip(tooltipTriggerEl)
  );

  // Keep track of currently open dropdown
  let currentOpenDropdown = null;
  let currentOpenButton = null;

  function initializeMultiselectDropdown(dropdownButton) {
    if (!dropdownButton) return;

    const dropdownMenu = dropdownButton.nextElementSibling;
    const dropdown = new bootstrap.Dropdown(dropdownButton);

    // Toggle dropdown on button click
    dropdownButton.addEventListener("click", (e) => {
      e.stopPropagation();

      // If clicking a different button than the currently open one
      if (currentOpenButton && currentOpenButton !== dropdownButton) {
        currentOpenDropdown.hide();
        dropdown.show();
        currentOpenDropdown = dropdown;
        currentOpenButton = dropdownButton;
      }
      // If clicking the same button that's currently open
      else if (currentOpenButton === dropdownButton) {
        dropdown.hide();
        currentOpenDropdown = null;
        currentOpenButton = null;
      }
      // If no dropdown is currently open
      else {
        dropdown.show();
        currentOpenDropdown = dropdown;
        currentOpenButton = dropdownButton;
      }
    });

    // Update tracking when dropdown is hidden (e.g., by clicking outside)
    dropdownButton.addEventListener("hidden.bs.dropdown", () => {
      if (currentOpenButton === dropdownButton) {
        currentOpenDropdown = null;
        currentOpenButton = null;
      }
    });
  }

  function initializeCarrierDropdown(dropdownButton){

    // Handle checkbox changes
    $(dropdownButton)
      .closest(".dropdown")
      .find(".form-check-input")
      .on("change", function () {
        const dropdown = $(this).closest(".dropdown");
        const button = dropdown.find(".btn");
        button.addClass("table-warning");
        check_unsaved();

        if (button.data('dup-tag')){
          carrier = this.value;
          existing_dup_rows = $('tr[data-index="'+carrier+'"][data-dup-tag="'+button.data('dup-tag')+'"]');
          if ((existing_dup_rows.length > 0) && ($(this).is(':checked'))){
            existing_dup_rows.each(function(){
              if ($(this).hasClass('table-danger')){
                $(this).find(".parameter-delete").click();
              }
              
            });
          } else if (existing_dup_rows.length > 0) {
            existing_dup_rows.each(function(){
              $(this).find(".parameter-delete").click();
            });
          } else if ($(this).is(':checked')) {
            dup_parameter_rows(button.attr('data-dup-tag'),carrier,'carriers');
          }
          if (button.data('dup-tag') == 'multi_carrier_out'){
						dup_row_units(button.data('dup-tag'),carrier,$(this).attr('rate_unit'),$(this).attr('quantity_unit'),false);
					} else if (button.data('dup-tag') == 'multi_carrier_in'){
						dup_row_units(button.data('dup-tag'),carrier,$(this).attr('rate_unit'),$(this).attr('quantity_unit'),true);
					}
        }

        if ($(this).val() == "-- New Carrier --") {
          $("#carriersModal").dialog();
          $(o).html(carrier);
          button.append(o);
        }
      });
  }

  function activate_carrier_multiselects() {
    $(".param_multiselect").each(function () {
        initializeMultiselectDropdown(this);
        if ($(this).hasClass('carrier_multi')){
          initializeCarrierDropdown(this);
        }
    });

    // Close dropdowns when clicking outside
    $(document).on("click", function (e) {
      if (!$(e.target).closest(".dropdown").length && currentOpenDropdown) {
        currentOpenDropdown.hide();
        currentOpenDropdown = null;
        currentOpenButton = null;
      }
    });

    // Handle escape key
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && currentOpenDropdown) {
        currentOpenDropdown.hide();
        currentOpenDropdown = null;
        currentOpenButton = null;
      }
    });
  }
  activate_carrier_multiselects();
  
  function parseDataValue(value) {
    if (!value) return [];
    if (value.startsWith("[")) {
      // Remove brackets and split by comma
      return value
        .slice(2, -2) // Remove ['...']
        .split("', '") // Split into array
        .map((item) => item.trim());
    }
    return [value];
  }
  $(".param_multiselect").each(function () {
    const dataValue = $(this).data("value");
    const selectedValues = parseDataValue(dataValue);
    
    // Find checkboxes in this dropdown
    $(this)
      .next(".dropdown-menu")
      .find(".form-check-input")
      .each(function () {
        const checkboxValue = $(this).val();
        if (selectedValues.includes(checkboxValue)) {
          $(this).prop("checked", true);
        }
      });
  });
});
