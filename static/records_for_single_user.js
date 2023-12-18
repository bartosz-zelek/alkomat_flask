function set_record_updater(user_id) {
    setInterval(() => {
        fetch(`/api/get_readings/${user_id}?count=20`)
            .then(response => response.json())
            .then(data => {
                let table = document.getElementById('UserRecordsTableBody');
                table.innerHTML = '';
                data.forEach((reading, index) => {
                    let row = document.createElement('tr');
                    row.innerHTML = `
                    <th scope="row">${index + 1}</th>
                    <td>${reading[0]}</td>
                    <td>${reading[1]} ${reading[2]}</td>
                    <td>${reading[3]}‰</td>
                    <td>${reading[3] < 0.2 ? "Admitted" : "Not admitted"}</td>
                    `;
                    if (reading[3] < 0.2) {
                        row.classList.add('table-success');
                    } else {
                        row.classList.add('table-danger');
                    }
                    table.appendChild(row);
                });
            });
    }, 1000);
}