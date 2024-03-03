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
        var fromDate = $("#select-date1").val();
        var toDate = $("#select-date2").val();
      
        fetch("/adm-data", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                fromDate: fromDate,
                toDate: toDate,
            }),
        })
        .then((response) => response.json())
        .then((data) => {
            updateCardValues(data);
        });
    });
    function updateCardValues(data) {
        // Оновлення значень карточок з даними
        $(".profit-card .card-text").text(data.profit + "₴");
        $(".operations-card .card-text").text(data.operations);
        $(".buy-rate-card .card-text").text(data.buy_rate + "₴");
        $(".sell-rate-card .card-text").text(data.sell_rate + "₴");
        
    }
  });