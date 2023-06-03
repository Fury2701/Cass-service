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
      
        fetch("/get_operations", {
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
            const sellTransactionsTable = document.getElementById("history");
            sellTransactionsTable.innerHTML = ""; // очистка таблицы
      
            const headerRow = document.createElement("tr");
            const headers = ["Дата", "Номер кассы", "Тип операции", "Валюта", "Сумма", "Сумма грн", "Курс"];
            headers.forEach((headerText) => {
              const header = document.createElement("th");
              header.textContent = headerText;
              headerRow.appendChild(header);
            });
            sellTransactionsTable.appendChild(headerRow);
      
            const tbody = document.createElement("tbody");
            data.forEach((transaction) => {
              const row = document.createElement("tr");
      
              const dateCell = document.createElement("td");
              dateCell.textContent = transaction.date;
              row.appendChild(dateCell);
      
              const cassIdCell = document.createElement("td");
              cassIdCell.textContent = transaction.cass_id;
              row.appendChild(cassIdCell);
      
              const operationTypeCell = document.createElement("td");
              operationTypeCell.textContent = transaction.operation_type;
              row.appendChild(operationTypeCell);
      
              const currencyCell = document.createElement("td");
              currencyCell.textContent = transaction.currency;
              row.appendChild(currencyCell);
      
              const amountCell = document.createElement("td");
              amountCell.textContent = transaction.amount.toFixed(1);
              row.appendChild(amountCell);
      
              const totalAmountCell = document.createElement("td");
              totalAmountCell.textContent = transaction.total_amount.toFixed(1);
              row.appendChild(totalAmountCell);
      
              const ratecell = document.createElement("td");
              ratecell.textContent = transaction.rate.toFixed(1);
              row.appendChild(ratecell);
      
              tbody.appendChild(row);
            });
      
            sellTransactionsTable.appendChild(tbody);
          });
      });
      

   /* $("#get-data-excel").click(function() {
        var fromDate = $("#select-date1").val();
        var toDate = $("#select-date2").val();
        // Добавьте вашу логику для получения данных в Excel
        // ...
    });*/
});