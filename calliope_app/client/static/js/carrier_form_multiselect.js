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

  function initializeCarrierDropdown(carrierId) {
    const dropdownButton = document.getElementById(`carrier-${carrierId}`);
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

    // Handle checkbox changes
    $(`#carrier-${carrierId}`)
      .closest(".dropdown")
      .find(".form-check-input")
      .on("change", function () {
        const button = $(this).closest(".dropdown").find(".btn");
        button.addClass("table-warning");
        check_unsaved();

        if (
          button.hasClass("units_in_selector") ||
          button.hasClass("units_out_selector")
        ) {
          const in_sel = $(".units_in_selector").first();
          const carrier_in = {
            name: in_sel.text(),
            rate_unit: in_sel.find("input:checked").data("rate"),
            quantity_unit: in_sel.find("input:checked").data("quantity"),
          };

          const out_sel = $(".units_out_selector").first();
          const carrier_out = {
            name: out_sel.text(),
            rate_unit: out_sel.find("input:checked").data("rate"),
            quantity_unit: out_sel.find("input:checked").data("quantity"),
          };

          update_carriers(carrier_in, carrier_out, false);
        }

        if ($(this).val() == "-- New Carrier --") {
          $("#carriersModal").dialog();
          $(o).html(carrier);
          button.append(o);
        }
      });
  }

  function activate_carrier_dropdowns() {
    $(".tech_carrier").each(function () {
      const carrierId = $(this).attr("id").split("-")[1];
      if (carrierId) {
        initializeCarrierDropdown(carrierId);
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

  activate_carrier_dropdowns();

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
  $(".tech_carrier").each(function () {
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
