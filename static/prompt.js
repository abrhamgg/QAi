
function searchTranscripts(searchStr, transcripts) {
  let lowerCaseSearchStr = searchStr.toLowerCase();
  // remove $ and # from search string
  lowerCaseSearchStr = lowerCaseSearchStr.replace(/[$#]/g, '');
  return transcripts
    .filter(entry => entry.text.toLowerCase().includes(lowerCaseSearchStr) || entry.text.includes(lowerCaseSearchStr.split(' ').join('')))
    .map(entry => ({
      text: entry.text,
      start: entry.start,
      end: entry.end
    }));
}

function searchTranscriptsByList(searchList, transcripts) {
  //remove duplicates and conjuctions
  searchList = searchList.filter((item, index) => searchList.indexOf(item) === index && !['and', 'or', 'to', 'no', 'TO', 'AND', 'NO', 'in', 'IN', 'BE', 'be'].includes(item));
  return searchList.map(searchStr => searchTranscripts(searchStr, transcripts)).flat();
}
document.getElementById('fileUpload').addEventListener('change', function() {
  var file = this.files[0];
  document.getElementById('uploadedScriptFileName').textContent = file.name;
  var flashMessage = document.getElementById('flashMessage');
  
  if (file.size > 5 * 1024 * 1024) { // 5MB size limit
      flashMessage.textContent = 'File size exceeds 5MB.';
      flashMessage.className = 'alert alert-danger mt-2';
      flashMessage.style.display = 'block';
      this.value = ''; // Clear the input
      return;
  } else {
      flashMessage.style.display = 'none';
  }
  
  var reader = new FileReader();
  reader.onload = function(e) {
      var pdfData = e.target.result;
      var loadingTask = pdfjsLib.getDocument({data: pdfData});
    //   get the file name
      
      loadingTask.promise.then(function(pdf) {
          var totalPages = pdf.numPages;
          console.log('Total pages: ' + totalPages);
          var textPromises = [];

          for (let i = 1; i <= totalPages; i++) {
              textPromises.push(pdf.getPage(i).then(page => {
                  return page.getTextContent().then(textContent => {
                      return textContent.items.map(item => item.str).join(' ');
                  });
              }));
          }
        //   weite function which adds all 
          

          Promise.all(textPromises).then(texts => {
              document.getElementById('callScripts').value = texts.join('\n\n');
              const num_chars = texts.join('\n\n').length;
              console.log('Number of characters: ' + num_chars);
              let maxLength = 256000;  // Set the maximum number of characters allowed
              let textArea = document.getElementById('callScripts');
              let charRemaining = document.getElementById('charRemaining');
              if (num_chars > maxLength) {
                  flashMessage.textContent = 'Exceeded maximum length of ' + maxLength + ' characters.';
                  flashMessage.className = 'alert alert-danger mt-2';
                  flashMessage.style.display = 'block';
                  return;
              }

            // Initialize character count
            charRemaining.textContent = maxLength;
            // char remaining must be max length - textArea.value.length
            charRemaining.textContent = maxLength - textArea.value.length;

              flashMessage.textContent = 'File uploaded and processed successfully.';
              flashMessage.className = 'alert alert-success mt-2';
              flashMessage.style.display = 'block';


              setTimeout(function() {
                  flashMessage.style.display = 'none';
              }, 5000);
          });
      }).catch(function(error) {
          flashMessage.textContent = 'An error occurred while processing the PDF.';
          flashMessage.className = 'alert alert-danger mt-2';
          flashMessage.style.display = 'block';
      });
  };
  reader.readAsArrayBuffer(file);
  
  // remove flash message after 5 seconds
  setTimeout(function() {
      flashMessage.style.display = 'none';
  }, 5000);
});


function rateCall(rating, contact_id) {
    // Hide the rating system
    document.querySelector('.rating-system-content').style.display = 'none';
    document.getElementById('spinner-feedback').style.display = 'block'
    // Show the flash message
    var flashMessage = document.getElementById('flash-message');
    flashMessage.textContent = 'Thank you for your feedback';
    flashMessage.classList.add('show');
    flashMessage.style.display = 'block'

    fetch('/dynamo/rating',{
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ contact_id: contact_id, rating: rating }),
    }).then(response => response.json())
    .then(data => {
        if (data.error) {
            flashMessage.textContent = data.error;
            flashMessage.className = 'alert alert-danger mt-2';
            document.getElementById('spinner-feedback').style.display = 'none'
            setTimeout(function() {
                flashMessage.style.display = 'none';
        
        
            }, 3000);
        } else {
            flashMessage.textContent = 'Rating submitted successfully';
            flashMessage.className = 'alert alert-success mt-2';
            document.getElementById('spinner-feedback').style.display = 'none'
            setTimeout(function() {
                flashMessage.style.display = 'none';
        
        
            }, 3000);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });


    
}



// COACHING RELATED FUNCTIONS //



function getScripts() {
    return new Promise((resolve, reject) => {
        fetch('/dynamo/get-scripts')
        .then(response => response.json())
        .then(data => {
            resolve(data);
        })
        .catch(error => {
            reject(error);
        });
    });
}

document.addEventListener('DOMContentLoaded', function() {

    getScripts().then(data => {
        console.log(data); // Log the data to understand its structure

        if (typeof data === 'object' && data !== null) {
            const availableScripts = document.getElementById('availableScripts');
            for (const scriptName in data) {
                if (data.hasOwnProperty(scriptName)) {
                    const option = document.createElement('option');
                    option.textContent = scriptName;
                    option.value = data[scriptName]; // Use the script name as the value
                    availableScripts.appendChild(option);

                }
            }
        } else {
            console.error('Data is not an object:', data);
        }
    }).catch(error => {
        console.error('Error fetching scripts:', error);
    });
});
function checkScrptLength(remaining) {
    const maxLength = 256000;  // Set the maximum number of characters allowed
    if (remaining < 0) {
        console.log('Exceeded maximum length of ' + maxLength + ' characters.');
        const flashMessage = document.getElementById('flashMessage');
        flashMessage.textContent = 'Exceeded maximum length of ' + maxLength + ' characters.';
        flashMessage.className = 'alert alert-danger mt-2';
        flashMessage.style.display = 'block';
    } else {
        document.getElementById('flashMessage').style.display = 'none';
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const textArea = document.getElementById('callScripts');
    const maxLength = 256000;  
    textArea.addEventListener('input', function() {
        let charRemaining = document.getElementById('charRemaining');

        let remaining = maxLength - textArea.value.length;
        charRemaining.textContent = remaining;
        
        checkScrptLength(remaining);
    });
});

// populate script based on the selected script
document.getElementById('availableScripts').addEventListener('change', function() {
    const selectedScriptContent = this.value;
    const callScriptsTextarea = document.getElementById('callScripts');
    callScriptsTextarea.value = selectedScriptContent;
    let maxLength = 256000;  // Set the maximum number of characters allowed
    let textArea = document.getElementById('callScripts');
    let charRemaining = document.getElementById('charRemaining');

    // Initialize character count
    charRemaining.textContent = maxLength;
    // char remaining must be max length - textArea.value.length
    charRemaining.textContent = maxLength - textArea.value.length;

    checkScrptLength(charRemaining)



    
});

function getSelectedBooks() {
    try{
        const selectedBooksDiv = document.getElementById('selectedBooks');
        const spans = selectedBooksDiv.getElementsByTagName('span');
        const books = [];

        for (let i = 0; i < spans.length; i++) {
            if (spans[i].textContent != 'x' && spans[i].querySelector('.remove')) {
                // remove last char
                const newTextContent = spans[i].textContent.slice(0, -1);
                books.push(newTextContent)
            }
        }
        // remove x from the list
        
        return books;
    }
    catch {
        console.log("error")
        return ''
    }
}
// write a function with promise to update the script by sending post request to /dynamo/update-script
function updateScript(script_name, script_content) {
    if (script_name == '' || script_content == '') {
        return
    }
   
    // get the available scripts from the dropdown
    const availableScripts = document.getElementById('availableScripts');
    const options = availableScripts.getElementsByTagName('option');
    for (let i = 0; i < options.length; i++) {
        if (options[i].textContent == script_name) {
            return;
        }
    }
    const scriptData = {
        "script": {
            "script_name": script_name,
            "script_content": script_content
        }
    }
    return new Promise((resolve, reject) => {
        fetch('/dynamo/update-script', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(scriptData)
        })
        .then(response => response.json())
        .then(data => {
            resolve(data);
        })
        .catch(error => {
            reject(error);
        });
    });
}

function startCoaching() {
    
    $('#spinner').show();
    const transcription = '{{contact.transcription | tojson | safe}}'
    const callScripts = $('#callScripts').val();
    const feedBackElement = document.getElementById('feedback');
    const file_name = document.getElementById('uploadedScriptFileName').textContent;
    // get the selected sales books from this element <div class="selected-books" id="selectedBooks"><label for="selectedBooks" class="form-label">Selected books:</label></div>
    let salesBooks = getSelectedBooks();

    const num_char = callScripts.length;
    if (num_char > 256000) {
        $('#spinner').hide();
        $('#flashMessage').text('Exceeded maximum length of 256000 characters.');
        $('#flashMessage').addClass('alert alert-danger mt-2');
        $('#flashMessage').show();
        return;
    }

    $.ajax({
        url: '/start-coaching',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            transcription: transcription,
            sales_books: salesBooks,
            call_scripts: callScripts
        }),
        success: function(response) {
            $('#spinner').hide();
            updateScript(file_name, callScripts)


            response = response.messages;

            let formattedResponse = `
                <div class="card mt-3">
                    <div class="card-body">
                        <h5 class="card-title">Coaching Feedback</h5>
                        <p class="card-text">${marked.parse(response.response)}</p>
                    </div>
                </div>
            `;

            $('#result').html(formattedResponse);
        },
        error: function (response) {
            console.log(response);
            $('#spinner').hide();
            // feedBackElement.value = 'An error occurred while generating feedback.';
            $('#result').html('<pre>' + JSON.stringify(response, null, 2) + '</pre>');
        }
    });
}



function openDeleteModal() {
    // Clear previous error messages
    document.getElementById('deleteError').style.display = 'none';
    
    // Populate the modal with scripts from the dropdown
    populateDeleteModalFromDropdown();
    
    // Show the modal
    new bootstrap.Modal(document.getElementById('deleteScriptModal')).show();
}

function populateDeleteModalFromDropdown() {
    const dropdown = document.getElementById('availableScripts');
    const scriptsList = document.getElementById('deleteScriptsList');
    
    scriptsList.innerHTML = ''; // Clear previous list
    
    Array.from(dropdown.options).forEach(option => {
        if (option.value) { // Skip the empty option
            const scriptItem = document.createElement('div');
            scriptItem.classList.add('form-check');
            
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.classList.add('form-check-input');
            checkbox.value = option.text; // Use script name for value
            checkbox.id = `script-${option.value}`;
            
            const label = document.createElement('label');
            label.classList.add('form-check-label');
            label.setAttribute('for', checkbox.id);
            label.textContent = option.text; // Display script name
            
            scriptItem.appendChild(checkbox);
            scriptItem.appendChild(label);
            
            scriptsList.appendChild(scriptItem);
        }
    });
}
function deleteSelectedScripts() {
    const selectedScripts = [];
    document.querySelectorAll('#deleteScriptsList input:checked').forEach(checkbox => {
        selectedScripts.push(checkbox.value); // Collect script names
    });
    console.log(selectedScripts);
    
    if (selectedScripts.length === 0) {
        document.getElementById('deleteError').textContent = 'No scripts selected.';
        document.getElementById('deleteError').style.display = 'block';
        return;
    }

    fetch('/dynamo/delete-scripts', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ script_names: selectedScripts }) // Send script names
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const modalElement = document.getElementById('deleteScriptModal');
            const modal = bootstrap.Modal.getInstance(modalElement);
            if (modal) {
                modal.hide(); // Hide the modal
            }
        

            refreshDropdown(); // Optionally refresh dropdown list

            
        } else {
            document.getElementById('deleteError').textContent = 'Failed to delete scripts.';
            document.getElementById('deleteError').style.display = 'block';
        }
    })
    .catch(error => {
        console.error('Error deleting scripts:', error);
        document.getElementById('deleteError').textContent = 'Failed to delete scripts.';
        document.getElementById('deleteError').style.display = 'block';
    });
}


function refreshDropdown() {
    fetch('/dynamo/get-scripts')
        .then(response => response.json())
        .then(data => {
            console.log(data); // Log the data to understand its structure
            const dropdown = document.getElementById('availableScripts');
            dropdown.innerHTML = '<option value="">Select a script</option>'; // Reset dropdown
            
            Object.keys(data).forEach(scriptName => {
                const option = document.createElement('option');
                option.value = scriptName; // Use script name as value
                option.textContent = scriptName; // Display script name
                dropdown.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error refreshing dropdown:', error);
        });
}

// function updateModal() {
//     fetch('/dynamo/get-scripts')
//         .then(response => response.json())
//         .then(data => {
//             console.log(data); // Log the data to understand its structure
//             const modal = document.getElementById('deleteScriptModal'); // Adjust ID based on your modal
//             const modalContent = modal.querySelector('.modal-body'); // Adjust selector based on your modal content
//             modalContent.innerHTML = ''; // Clear existing content
            
//             Object.keys(data).forEach(scriptName => {
//                 const item = document.createElement('div');
//                 item.textContent = scriptName; // Display script name in the modal
//                 modalContent.appendChild(item);
//             });
//             // Reinitialize any required Bootstrap modal or event listeners
//             // Example for Bootstrap modals:
            
//         })
//         .catch(error => {
//             console.error('Error updating modal:', error);
//         });
// }