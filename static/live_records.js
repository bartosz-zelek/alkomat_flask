// Add an image cache to prevent refetching and blinking
let imagesCache = {};

setInterval(() => {
    fetch('/api/get_readings?count=20')
        .then(response => response.json())
        .then(data => {
            let table = document.getElementById('liveRecordsTableBody');
            table.innerHTML = '';
            data.forEach((reading, index) => {
                const [time, firstName, lastName, value, uuid, date] = reading;
                // Determine image content: cached or loading placeholder
                let imgContent;
                if (imagesCache[uuid]) {
                    imgContent = `<img src="data:image/png;base64,${imagesCache[uuid]}" alt="User Image" width="100">`;
                } else {
                    imgContent = 'Loading...';
                    // fetch once and store in cache
                    fetch(`/api/get_image?uuid=${uuid}`)
                        .then(res => res.json())
                        .then(imgData => { imagesCache[uuid] = imgData.base64; });
                }

                let row = document.createElement('tr');
                row.innerHTML = `
                <th scope="row">${index + 1}</th>
                <td>${firstName}</td>
                <td>${lastName}</td>
                <td>${value}‰</td>
                <td>${value < 0.2 ? "Dopuszczony" : "Niedopuszczony"}</td>
                <td>${date}</td>
                <td>${imgContent}</td>
                `;
                row.classList.add(value < 0.2 ? 'table-success' : 'table-danger');
                table.appendChild(row);
            });
        });
}, 1000);