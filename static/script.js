HIGHLEVEL_BASE_URL="https://rest.gohighlevel.com/v1"

document.addEventListener("DOMContentLoaded", function() {
   masterFunction("get");
//    document.getElementById("reloadButton").addEventListener("click", function(){
//     masterFunction("get");
//    });
   let selectedWorkspace = document.getElementById("customValueDropdown")
    selectedWorkspace.addEventListener("change", function(){
        document.getElementById("spinner").style.display = "block";

        masterFunction("get");
    });

    document.getElementById("sendPostRequestBtn").addEventListener("click", function(){
        this.disabled = true;
        sendPostRequest()
        setTimeout(() => {
            this.disabled = false;
        }, 3000);
    });

    function sendPostRequest() {
        // let promptField = document.getElementById("prompt-field").value;
        let goalField = document.getElementById("goal").value;
        let ruleField = document.getElementById("rule").value;
        let prompt = combinePrompt(goalField, ruleField);
        let workspace = document.getElementById("customValueDropdown").value;
        let newdata = {}
        fetch('/highlevel/customValues')
        .then(response => response.json())
        .then(data =>{
            const customValues = data.customValues;
            let count = 0;
            for (let customValue of customValues) {
                if (customValue.name === workspace && customValue.value !== prompt) {
                    newdata["name"]= customValue.name;
                    newdata["value"] = prompt;
                    fetch('/highlevel/customValues/' + customValue.id, {
                        method: 'put',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(newdata),
                    }).then(response => {
                        if (response.status === 200) {
                            displayFlashMessage("Custom value updated successfully", "success");
                            count++;
                            return;
                        } else {
                            displayFlashMessage("Failed to update custom value", "danger");
                            return;
                        }
                    
                    })
                } else if (customValue.name === workspace && customValue.value === prompt) {
                    displayFlashMessage("No changes made", "info");
                    return;

                }
            }
        })
    }
});

function masterFunction(flag) {
    let selectedWorkspace = document.getElementById("customValueDropdown").value;

    // get the custom values for the selected workspace
    fetch('/highlevel/customValues')
    .then(response => response.json())
    .then(data => {
        console.log(data)
        if (flag === "get" ){            
            const customValues = data.customValues;
        for (let customValue of customValues) {
            if (customValue.name === selectedWorkspace) {
                //  select the prompt field
                // var promptField = document.getElementById("prompt-field");
                // promptField.innerHTML = customValue.value;

                // console.log(splitPrompt(customValue.value));
                
                // console.log(combinePrompt(splitPrompt(customValue.value)[0], splitPrompt(customValue.value)[1]));

                // select the goal field
                // stop the spinner
                let goalField = document.getElementById("goal");
                let ruleField = document.getElementById("rule");

                const [goal, rule] = splitPrompt(customValue.value);
                goalField.value = goal;
                ruleField.value = rule;
            }
        }

        // send flash message to the user'
        displayFlashMessage("Custom values loaded successfully", "success"); 
        document.getElementById("spinner").style.display = "none";

        }
               
    });
}
function redirectToHomePage() {
    window.location.href = "/";
}


function displayFlashMessage(message, type) {
    let flashMessage = document.createElement('div');
    flashMessage.classList.add('alert', 'alert-' + type);
    flashMessage.textContent = message;

    // Add fixed positioning to the flash message container
    let flashContainer = document.getElementById('flashMessages');
    flashContainer.style.position = 'fixed';
    flashContainer.style.top = '0';
    flashContainer.style.width = '30%';
    flashContainer.style.zIndex = '9999';

    flashContainer.appendChild(flashMessage);

    // Set a timeout to remove the flash message after 3 seconds
    setTimeout(function() {
        flashMessage.remove();
    }, 3000);
}

function splitPrompt(prompt) {
    const parts = prompt.split("RULES");
    const goal = parts[0].replace("GOAL:", "").trim();
    const rule = parts[1].replace("RULES:", "").trim();
    return [
        "GOAL: " + goal,
        "RULE: " + rule
    ];
}

function combinePrompt(goal, rule) {
    const goalText = goal.replace("GOAL: ", "").trim();
    const ruleText = rule.replace("RULE: ", "").trim();
    return `GOAL: ${goalText} RULES ${ruleText}`;
}