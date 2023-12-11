setInterval(() => {
    debugger;
    fetch('/registered_workers')
        .then(response => response.json())
        .then(data => {
            let table = document.getElementById('workers');
            table.innerHTML = '';
            data.forEach((employee, index) => {
                let row = document.createElement('tr');
                row.innerHTML = `
                <th scope="row">${index + 1}</th>
                <td>${employee[1]}</td>
                <td>${employee[2]}</td>
                <td>
                    <form action="/block_employee" method="post" class="d-inline">
                        <input type="hidden" name="id" value="${employee[0]}">
                        <button type="submit" class="btn btn-danger" id="blockButton${employee[0]}">Block</button>
                    </form>
                    <form action="/unblock_employee" method="post" class="d-inline">
                        <input type="hidden" name="id" value="${employee[0]}">
                        <button type="submit" class="btn btn-success" id="unblockButton${employee[0]}">Unblock</button>
                    </form>
                </td>
                `;
                if (employee[3] == 1) {
                    row.classList.add('table-danger');
                }
                table.appendChild(row);
            });
        });
}, 2000);