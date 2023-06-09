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
          const headers = ["Дата", "Номер каси", "Тип операції", "Валюта", "Сума валюти", "Сума в грн", "Курс"];
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

                            // Добавление класса к строке в зависимости от значения "Тип операції"
              if (transaction.operation_type === "Купівля") {
                    row.classList.add("buy-transaction"); // добавление класса "buy-transaction"
              } else if (transaction.operation_type === "Продаж") {
                    row.classList.add("sell-transaction"); // добавление класса "sell-transaction"
              }
    
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
    
  // Обработчик для загрузки файла
  function downloadFile(url) {
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', '');
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
  }

  $("#get-data-excel").click(function() {
      var fromDate = $("#select-date1").val();
      var toDate = $("#select-date2").val();
      fetch("/get_operations_excel", {
          method: "POST",
          headers: {
              "Content-Type": "application/json",
          },
          body: JSON.stringify({
              fromDate: fromDate,
              toDate: toDate,
          }),
      })
      .then((response) => {
          if (!response.ok) {
              throw new Error("Помилка отримання даних: " + response.status);
          }
          return response.blob();
      })
      .then((blob) => {
          // Проверяем тип ответа
          var contentType = blob.type;
          if (contentType === "application/json") {
              return blob.text().then((text) => {
                  var errorResponse = JSON.parse(text);
                  throw new Error("Помилка: " + errorResponse.message);
              });
          }
          // Создаем объект URL для файла
          const url = URL.createObjectURL(blob);
          // Загружаем файл
          downloadFile(url);
          // Освобождаем ресурсы URL
          URL.revokeObjectURL(url);
      })
      .catch((error) => {
          // Выводим уведомление об ошибке
          console.error(error);
          alert(error.message);
      });
  });
});
