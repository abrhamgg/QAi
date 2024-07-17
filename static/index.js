$(function() {
    // Initialize datepickers
    $('#filterStartDate, #filterEndDate').datepicker({
        format: 'yyyy-mm-dd',
        autoclose: true
    });

    // Initialize DataTable
    var table = $('#dataTable').DataTable({
        "pageLength": 10,
        "dom": '<"top">rt<"bottom"lfip>',
        "searching": true
    });

    $('#dataTable_filter').hide();

    // Initialize slider
    var $filterCallDuration = $('#filterCallDuration');
    var $filterCallDurationValue = $('#filterCallDurationValue');
    var durationValues = [2, 5, 10, 20, 30];

    $filterCallDuration.on('input', function() {
        var index = parseInt($(this).val());
        var value = durationValues[index];
        $filterCallDurationValue.text(value + " minutes");
    });

    // Filter function
    function filterTable() {
        var startDate = $('#filterStartDate').val();
        var endDate = $('#filterEndDate').val();
        var callDurationIndex = parseInt($('#filterCallDuration').val());
        var callDuration = durationValues[callDurationIndex];

        $.fn.dataTable.ext.search.push(
            function(settings, data, dataIndex) {
                var date = new Date(data[1]); // use data for the date column
                var duration = data[6]; // use data for the call duration column

                // Extract minutes from the duration string (assuming format is HH:MM:SS)
                var durationMinutes = parseInt(duration.split(':')[1]);

                if (
                    (startDate === "" || date >= new Date(startDate)) &&
                    (endDate === "" || date <= new Date(endDate)) &&
                    (durationMinutes === callDuration)
                ) {
                    return true;
                }
                return false;
            }
        );

        table.draw();
        $.fn.dataTable.ext.search.pop();
    }

    // Apply filter when slider changes
    $filterCallDuration.on('change', function() {
        filterTable();
    });

    // Apply filter when date inputs change
    $('#filterStartDate, #filterEndDate').on('change', function() {
        filterTable();
    });

    // Apply filter when button is clicked
    $('#applyFilters').click(function() {
        filterTable();
        $('#filterModal').modal('hide');
    });

    // Clear filters
    $('#clearFilters').click(function() {
        $('#filterStartDate').val('');
        $('#filterEndDate').val('');
        $('#filterCallDuration').val(0);
        $filterCallDurationValue.text("2 minutes");
        table.search('').columns().search('').draw();
    });

    // Initialize tooltips
    $('[data-toggle="tooltip"]').tooltip();

    // Open filter modal
    $('#openFilterModal').click(function() {
        $('#filterModal').modal('show');
    });

    // Search functionality
    $('#dataTableSearch').keyup(function() {
        table.search($(this).val()).draw();
    });
});
