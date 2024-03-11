$(document).ready(function() {
    $("#select-date1").datepicker({
        dateFormat: "yy-mm-dd",
        dayNamesMin: ["Нд", "Пн", "Вт", "Ср", "Чт", "Пт", "Сб"],
        monthNames: ["Січень", "Лютий", "Березень", "Квітень", "Травень", "Червень", "Липень", "Серпень", "Вересень", "Жовтень", "Листопад", "Грудень"],
        monthNamesShort: ["Січ", "Лют", "Бер", "Кві", "Тра", "Чер", "Лип", "Сер", "Вер", "Жов", "Лис", "Гру"]
    });
  
    $("#select-date2").datepicker({
        dateFormat: "yy-mm-dd",
        dayNamesMin: ["Нд", "Пн", "Вт", "Ср", "Чт", "Пт", "Сб"],
        monthNames: ["Січень", "Лютий", "Березень", "Квітень", "Травень", "Червень", "Липень", "Серпень", "Вересень", "Жовтень", "Листопад", "Грудень"],
        monthNamesShort: ["Січ", "Лют", "Бер", "Кві", "Тра", "Чер", "Лип", "Сер", "Вер", "Жов", "Лис", "Гру"]
    });
  
    $("#get-data").click(function() {
        var cass_id = $('#cass').val();
        var fromDate = $("#select-date1").val();
        var toDate = $("#select-date2").val();
      
        fetch("/graf-data", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                cass_id: cass_id,
                fromDate: fromDate,
                toDate: toDate,
            }),
        })
        .then((response) => response.json())
        .then((data) => {
            updateCharts(data);
        });
    });
    function updateCharts(data) {
        console.log(data)

        // Знищення попередніх графіків, якщо вони існують
        if (window.myChart) {
            window.myChart.destroy();
        }
        if (window.operationsChart) {
            window.operationsChart.destroy();
        }
    
        // Оновлення даних для графіку прибутку
        var ctxProfit = document.getElementById('myChart').getContext('2d');
        var datesProfit = data.profit.map(item => item[0]);
        var profits = data.profit.map(item => item[1]);
    
        window.myProfitChart = new Chart(ctxProfit, {
            type: 'line',
            data: {
                labels: datesProfit,
                datasets: [{
                    label: 'Прибуток за день',
                    data: profits,
                    fill: false,
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    
        // Оновлення даних для графіку операцій
        var ctxOperations = document.getElementById('operationsChart').getContext('2d');
        var datesOperations = Object.keys(data.operations);
        var numOperations = Object.values(data.operations);
        
    
        window.myOperationsChart = new Chart(ctxOperations, {
            type: 'line',
            data: {
                labels: datesOperations,
                datasets: [{
                    label: 'Кількість операцій за день',
                    data: numOperations,
                    fill: false,
                    borderColor: 'rgb(255, 99, 132)',
                    tension: 0.1
                }]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
  });