const cashierNumber = document.getElementById("cashier-number").textContent;

// Обновление таблицы балансов
function updateBalancesTable(cashierNumber) {
    fetch(`/update_balances/${cashierNumber}`)
      .then(response => response.json())
      .then(data => {
        const balancesTable = document.querySelector('.balances-container table');
        const tbody = balancesTable.querySelector('tbody');
        tbody.innerHTML = ''; // очистка таблицы
  
        // Создание строк таблицы с полученых данных
        data.forEach(balance => {
          const row = document.createElement('tr');
          const currencyCell = document.createElement('td');
          currencyCell.textContent = balance.currency;
          const balanceCell = document.createElement('td');
          balanceCell.textContent = balance.balance.toFixed(2); // Форматирование таблицы до сотых
          row.appendChild(currencyCell);
          row.appendChild(balanceCell);
          tbody.appendChild(row);
        });
      })
      .catch(error => {
        console.error(error);
        alert('Помилка при оновленні балансів');
      });
  }

  // Обновление данных таблицы selltransactions-table
  const updateSellTransactionsTable = (cashierNumber) => {
    const cassId = cashierNumber;
  
    fetch(`/incasationget?cass_id=${cassId}`)
      .then(response => response.json())
      .then(data => {
        const sellTransactionsTable = document.getElementById("history-table-container");
        sellTransactionsTable.innerHTML = ""; // очистка таблицы
  
        const table = document.createElement("table");
        table.classList.add("history-table");
  
        const thead = document.createElement("thead");
        const headerRow = document.createElement("tr");
        const headers = ["Дата", "Каси", "Валюта", "Сума операції", "Тип", "Ітоговий баланс"];
  
        headers.forEach(headerText => {
          const header = document.createElement("th");
          header.textContent = headerText;
          headerRow.appendChild(header);
        });
  
        thead.appendChild(headerRow);
        table.appendChild(thead);
  
        const tbody = document.createElement("tbody");
        data.forEach(transaction => {
          const row = document.createElement("tr");
  
          const dateCell = document.createElement("td");
          dateCell.textContent = transaction.date;
          row.appendChild(dateCell);
  
          const cassIdCell = document.createElement("td");
          cassIdCell.textContent = transaction.cass_id;
          row.appendChild(cassIdCell);
  
          const currencyCell = document.createElement("td");
          currencyCell.textContent = transaction.currency;
          row.appendChild(currencyCell);
  
          const amountCell = document.createElement("td");
          amountCell.textContent = transaction.amount.toFixed(1);
          row.appendChild(amountCell);

          const operationTypeCell = document.createElement("td");
          operationTypeCell.textContent = transaction.operation_type;
          row.appendChild(operationTypeCell);

          const totalAmountCell = document.createElement("td");
          totalAmountCell.textContent = transaction.total_amount.toFixed(1);
          row.appendChild(totalAmountCell);
  
          tbody.appendChild(row);
        });
  
        table.appendChild(tbody);
        sellTransactionsTable.appendChild(table);
  
        // Добавляем строку с заголовком
        const header = document.createElement("h2");
        header.textContent = "Історія Інкасацій/Підкріплень";
        sellTransactionsTable.insertBefore(header, table);
      })
      .catch(error => {
        console.error(error);
        alert("Помилка оновлення таблиці підкріплення/інкасації");
      });
  };  
  
  
// фунционал кнопки подкрепить
  const sellButton = document.querySelector('button[value="adding-button"]'); 
  sellButton.addEventListener('click', (event) => {
    event.preventDefault();
    const currencySelect = document.getElementById("currency");
    const selectedCurrency = currencySelect.value;
    const amountInput = document.getElementById("amount");
    const amount = parseFloat(amountInput.value);
  
    if (selectedCurrency && amount && cashierNumber) {
      const confirmationMessage = `Підтвердіть підкріплення ${amount.toFixed(2)} ${selectedCurrency}`;
      if (confirm(confirmationMessage)) {
         nth=`Ви впевнені, що хочете підкріпити ${amount.toFixed(2)} ${selectedCurrency}`;
         const proceed = confirm(nth);
        if (proceed) {
          const data = {
            currency: selectedCurrency,
            amount: amount.toFixed(2),
            cashier_number: cashierNumber // Добавление номера кассы к данным
          };
  
          fetch('/adding', {
            method: 'POST',
            body: JSON.stringify(data),
            headers: {
              'Content-Type': 'application/json',
            },
          })
            .then(response => response.json())
            .then(data => {
              if (data.success) {
                alert(data.message);
                // Вызов функции обновления балансов по валютах и передача в нее номера кассы
                updateBalancesTable(cashierNumber);
                updateSellTransactionsTable(cashierNumber); // Вызов функции обновления таблицы <=15 min
              } else {
                alert(data.message);
              }
            })
            .catch(error => {
              console.error(error);
              alert('Помилка підключення');
            });
        }
      }
    } else {
      alert('Будь ласка, виберіть валюту та вкажіть суму');
    }
  }); 