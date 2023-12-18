window.onload = function() {
    fetch('/api/get_plots')
    .then(response => {
        if(response.ok) {
            let soberReadingsHistogram = document.getElementById('soberReadingsHistogram');
            let blocksNumberHistogram = document.getElementById('blocksNumberHistogram');

            // Update the src attributes of the img tags
            soberReadingsHistogram.src = "/static/sober_readings_histogram.png";
            blocksNumberHistogram.src = "/static/blocks_number_histogram.png";
        }
    })
    .catch(error => console.error(error));
};
