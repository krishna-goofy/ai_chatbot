document.addEventListener("DOMContentLoaded", function() {
    hideLoadingAnimation(); // Ensure the loading animation is hidden on page load
    loadQuestionBubbles(); // Load predefined question bubbles from PHP
});

document.getElementById('send-btn').addEventListener('click', function() {
    sendMessage();
});

function sendMessage() {
    let question = document.getElementById('question-input').value;

    if (question) {
        appendUserMessage(question);
        document.getElementById('question-input').value = '';  // Clear the input field
        showLoadingAnimation();  // Show loading animation

        // Send request to Flask server
        fetch('/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question: question }),
        })
        .then(response => response.json())
        .then(data => {
            hideLoadingAnimation();  // Hide loading animation
            if (data.answer.includes('|')) { // Check for tabular data
                appendBotMessage(buildTable(data.answer));
            } else {
                appendBotMessage(data.answer);
            }
        })
        .catch(error => {
            hideLoadingAnimation();  // Hide loading animation on error
            appendBotMessage("Sorry, something went wrong.");
        });
    }
}
function showLoadingAnimation() {
    document.getElementById('loading-container').classList.remove('hidden');
}

function hideLoadingAnimation() {
    document.getElementById('loading-container').classList.add('hidden');
}

function appendUserMessage(message) {
    const chatBox = document.getElementById('chat-box');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'user-message';
    messageDiv.innerHTML = message;
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;  // Scroll to the bottom
}

function appendBotMessage(message) {
    const chatBox = document.getElementById('chat-box');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'bot-message';
    messageDiv.innerHTML = message;
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;  // Scroll to the bottom
}

function askPredefinedQuestion(question) {
    document.getElementById('question-input').value = question;
    sendMessage();
}

function buildTable(data) {
    const rows = data.split('\n');
    let table = '<table>';
    rows.forEach(row => {
        const cols = row.split('|');
        table += '<tr>';
        cols.forEach(col => {
            table += `<td>${col.trim()}</td>`;
        });
        table += '</tr>';
    });
    table += '</table>';
    return table;
}

function loadQuestionBubbles() {
    console.log("Loading question bubbles...");

    fetch('/get_predefined_questions')
        .then(response => {
            if (!response.ok) {
                throw new Error("Network response was not ok");
            }
            return response.json();
        })
        .then(questions => {
            console.log("Fetched questions:", questions);
            const questionBubbles = document.getElementById('question-bubbles');
            questions.forEach(question => {
                const button = document.createElement('button');
                button.className = 'question-btn';
                button.textContent = question;
                button.onclick = () => askPredefinedQuestion(question);
                questionBubbles.appendChild(button);
            });
        })
        .catch(error => {
            console.error('Error fetching predefined questions:', error);
        });
}

