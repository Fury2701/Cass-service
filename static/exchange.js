const cashierNumber = document.getElementById("cashier-number").textContent;

// Обновление данных таблицы selltransactions-table
const updateSellTransactionsTable = (cashierNumber) => {
  const cassId = cashierNumber;

  fetch(`/transactions?cass_id=${cassId}`)
    .then(response => response.json())
    .then(data => {
      const sellTransactionsTable = document.getElementById("selltransactions-table");
      sellTransactionsTable.innerHTML = ""; // очистка таблицы

      const headerRow = document.createElement("tr");
      const headers = ["Дата", "Номер каси", "Тип операції", "Валюта", "Сума", "Сума грн", "Курс", "Дії"];
      headers.forEach(headerText => {
        const header = document.createElement("th");
        header.textContent = headerText;
        headerRow.appendChild(header);
      });
      sellTransactionsTable.appendChild(headerRow);

      data.forEach(transaction => {
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

        const cancelCell = document.createElement("td");
        const cancelButton = document.createElement("button");
        cancelButton.className = "cancel-btn";
        cancelButton.dataset.transactionId = transaction.id;
        cancelButton.textContent = "Сторно";

        cancelCell.appendChild(cancelButton);
        row.appendChild(cancelCell);

        sellTransactionsTable.appendChild(row);
      });

      const cancelButtons = document.querySelectorAll('.cancel-btn');
      cancelButtons.forEach(button => {
        button.addEventListener('click', () => {
          const transactionId = button.dataset.transactionId;
          deleteTransaction(transactionId);
        });
      });
    })
    .catch(error => {
      console.error(error);
      alert("Ошибка при получении данных");
    });
};


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

// Обработчик события для кнопки "сторно"
document.addEventListener('DOMContentLoaded', () => {
  const cancelButtons = document.querySelectorAll('.cancel-btn');
  cancelButtons.forEach(button => {
    button.addEventListener('click', () => {
      const transactionId = button.dataset.transactionId;
      deleteTransaction(transactionId);
    });
  });
});

function deleteTransaction(transactionId) {
  const confirmMessage = 'Ви впевнені, що хочете виконати сторно цієї операції?';
  const proceed = confirm(confirmMessage);
  if (!proceed) {
    return;
  }

  fetch(`/transactions/${transactionId}`, {
    method: 'DELETE'
  })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        alert(data.message);
        // Вызов функции обновления балансов по валютам после успешного удаления операции
        updateBalancesTable(cashierNumber);
        updateSellTransactionsTable(cashierNumber);// Вызов функции обновления таблицы операций
      } else {
        alert(data.message);
      }
    })
    .catch(error => {
      console.error(error);
      alert('Помилка підключення');
    });
}



const saveButton = document.getElementById("savebutton");
saveButton.addEventListener('click', (event) => {
  event.preventDefault();
  const form = document.querySelector('form');
  const formData = new FormData(form);
  formData.append('cashier_number', cashierNumber); // Добавляем номер кассы в объект FormData
  const data = Object.fromEntries(formData);
  fetch('/save_courses', {
    method: 'POST',
    body: JSON.stringify(data),
    headers: {
      'Content-Type': 'application/json',
    },
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      const courses = data.courses;
      for (let i = 0; i < courses.length; i++) {
        const currency = courses[i].currency;
        const buyRate = courses[i].buy_rate;
        const sellRate = courses[i].sell_rate;
        const row = document.querySelector(`tr[data-currency="${currency}"]`);
        const buyRateCell = row.querySelector('td.buy-rate input');
        const sellRateCell = row.querySelector('td.sell-rate input');
        buyRateCell.value = buyRate.toFixed(2);
        sellRateCell.value = sellRate.toFixed(2);
      }
      alert(data.message);
    } else {
      alert(data.message);
    }
  })
  .catch(error => {
    console.error(error);
    alert("Error of cours tbl");
  });
});


const sellButton = document.querySelector('button[value="sell"]');// фунционал кнопки продать
sellButton.addEventListener('click', (event) => {
  event.preventDefault();
  const currencySelect = document.getElementById("currency");
  const selectedCurrency = currencySelect.value;
  const amountInput = document.getElementById("amount");
  const amount = parseFloat(amountInput.value);

  if (selectedCurrency && amount && cashierNumber) {
    const confirmationMessage = `Підтвердіть продаж ${amount.toFixed(2)} ${selectedCurrency}`;
    if (confirm(confirmationMessage)) {
      const courseRow = document.querySelector(`tr[data-currency="${selectedCurrency}"]`);
      const sellRateInput = courseRow.querySelector('td.sell-rate input');
      const sellRate = parseFloat(sellRateInput.value);

      const totalAmount = (amount * sellRate).toFixed(2);
      const confirmMessage = `Візьміть від клієнта ${totalAmount} грн`;
      const proceed = confirm(confirmMessage);
      if (proceed) {
        const data = {
          currency: selectedCurrency,
          amount: amount.toFixed(2),
          rate: sellRate.toFixed(2),
          totalAmount: totalAmount,
          cashier_number: cashierNumber // Добавление номера кассы к данным
        };

        fetch('/sell', {
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

const buyButton = document.querySelector('button[value="buy"]');// фунционал кнопки купить
buyButton.addEventListener('click', (event) => {
  event.preventDefault();
  const currencySelect = document.getElementById("currency");
  const selectedCurrency = currencySelect.value;
  const amountInput = document.getElementById("amount");
  const amount = parseFloat(amountInput.value);

  if (selectedCurrency && amount && cashierNumber) {
    const confirmationMessage = `Підтвердіть купівлю ${amount.toFixed(2)} ${selectedCurrency}`;
    if (confirm(confirmationMessage)) {
      const courseRow = document.querySelector(`tr[data-currency="${selectedCurrency}"]`);
      const buyRateInput = courseRow.querySelector('td.buy-rate input');
      const buyRate = parseFloat(buyRateInput.value);

      const totalAmount = (amount * buyRate).toFixed(2);
      const confirmMessage = `Віддайте клієнту ${totalAmount} грн`;
      const proceed = confirm(confirmMessage);
      if (proceed) {
        const data = {
          currency: selectedCurrency,
          amount: amount.toFixed(2),
          rate: buyRate.toFixed(2),
          totalAmount: totalAmount,
          cashier_number: cashierNumber // Добавление номера кассы к данным
        };

        fetch('/buy', {
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