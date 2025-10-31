function updateTime() {
    const date = new Date();
    const time = date.toLocaleTimeString(undefined, {hour: 'numeric', minute: 'numeric'});
    const day = date.toLocaleDateString(undefined, {weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'});
    document.getElementById('datetime').innerText = `${day} ${time}`;
}

document.addEventListener("DOMContentLoaded", async () => {
    const refreshButton = document.querySelector('#refreshButton');
    if (refreshButton){
        refreshButton.addEventListener('click', () => {
            location.reload();
        })
    }
    
    const response = await fetch('/api/report/smartlp', {
        method: 'GET'
    });
    const resp = await response.json();
    const data = resp.data;
    
    const logChart = document.getElementById('parsed-chart');
    new Chart(logChart, {
        type: 'pie',
        data: {
            labels: ['Parsed by SmartLP', 'Unparsed by SmartLP'],
            datasets: [{
                label: 'Number of Logs',
                data: [data.parsed, data.unparsed],
                backgroundColor: ['rgb(238, 75, 43)', 'rgb(63, 0, 255)'],
                borderWidth: 1
            }]
        },
    });
    const total = data.parsed + data.unparsed;
    const parseBody = document.querySelector("#logParsedTable tbody");
    parseBody.innerHTML = "";
    var row = parseBody.insertRow();
    row.insertCell(0).textContent = "Parsed by SmartLP";
    row.insertCell(1).textContent = `${data.parsed} (${(data.parsed / total * 100).toFixed(2)}%)`;
    row = parseBody.insertRow();
    row.insertCell(0).textContent = "Unparsed by SmartLP";
    row.insertCell(1).textContent = `${data.unparsed} (${(data.unparsed / total * 100).toFixed(2)}%)`;
    row = parseBody.insertRow();
    row.insertCell(0).textContent = "Total Unparsed in System";
    row.insertCell(1).textContent = `${data.unparsed + data.parsed}`;

    const statsBody = document.querySelector("#logStatsTable tbody");
    statsBody.innerHTML = "";
    for (i=0; i < data.logtypes.length; i++) {
        row = statsBody.insertRow();
        row.insertCell(0).textContent = data.logtypes[i][0];
        row.insertCell(1).textContent = data.logtypes[i][1];
    }

    setInterval(updateTime, 10000);
    updateTime();

    const saveBtn = document.querySelector("#saveButton");
    var options = {
        margin: 12,
        pagebreak: {before: ['#content2', '#content3']},
        filename: 'report.pdf',
        image: {type: 'png'},
        html2canvas: {
            scale: 2,
            scrollY: 0,
        }
    }
    if (saveBtn){
        saveBtn.addEventListener('click', async () => {
            await html2pdf().set(options).from(document.querySelector('.row'))
                .then(document.getElementById('content1').classList.add("d-flex")).save();
            document.getElementById('content1').classList.remove("d-flex");
        })
    }
})