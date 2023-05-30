// Using the listTabs() function in the browser console:
// listTabs((tabList) => console.log(tabList));

// Using the openNewTab() function in the browser console:
// openNewTab('https://example.com', (tab) => console.log('New tab opened:', tab));


function domToHTML() {
  const doctype = document.doctype;
  const doctypeString = doctype ? `<!DOCTYPE ${doctype.name}>` : '';
  const html = document.documentElement.outerHTML;
  return doctypeString + html;
}

// Listen for messages from the background script
browser.runtime.onMessage.addListener((message) => {
  if (message.action === 'getHTML') {
    return Promise.resolve(domToHTML());
  } else if (message.action === 'injectScript' && message.source) {
    return injectScript(message.source);
  } else if (message.action === 'waitForElement' && message.selector && message.timeout) {
    console.log("waitForElement message received in content script: " + message.selector + " timeout: " + message.timeout);
    return waitForElement(message.selector, message.timeout);
  }
});


function executeScript(source, token) {
  console.log("content.js executeScript() called" + " " + token + " " + source);
  const script = document.createElement('script');
  script.textContent = source;

  // Create a promise that will be resolved when the message is received
  const promise = new Promise((resolve, reject) => {
    function messageListener(event) {
      // Check for some condition to verify that this is the message you want to receive
      if (event.source === window && event.data.type && event.data.token === token) {
        if (event.data.type === 'FROM_PAGE_SCRIPT') {
          console.log('Received message from page script:', event.data.text);
          // Resolve the promise with the received message
          resolve(event.data.text);
        } else if (event.data.type === 'FROM_PAGE_SCRIPT_ERROR') {
          console.log('Received error from page script:', event.data.text);
          // Reject the promise with the received error
          // reject(new Error(event.data.text));
          resolve(event.data.text);
        }
        // Cleanup after receiving the message
        window.removeEventListener('message', messageListener);
        document.body.removeChild(script);
      }
    }

    window.addEventListener('message', messageListener, false);
  });

  document.body.appendChild(script);

  // Return the promise
  return promise;
}


function waitForElement(selector, timeout) {
  const token = Math.random().toString(36).substring(2);
  console.log('waitForElement() called in content script: ' + selector + ' ' + timeout + ' ' + token)

  const source = `
  window.result = null;
  waitForElement('` + selector + `', timeout = ` + timeout + `)
  .then(() => {
      console.log('Element found');
      window.result = true;
      window.postMessage({ type: 'FROM_PAGE_SCRIPT', token: '${token}', text: window.result }, '*');
  })
  .catch(() => {
      console.log('Element not found');
      window.result = false;
      window.postMessage({ type: 'FROM_PAGE_SCRIPT', token: '${token}', text: window.result }, '*');
  });
  
  `;
  
  return executeScript(source, token);
}

function injectScript(source) {
  // Generate a unique token for this script injection
  const token = Math.random().toString(36).substring(2);

  console.log('Injecting script:', source)

  // Append code to send a message with the value of window.result
  source = `window.result = null;
  window.onerror = function(message, url, line, column, error) {
    window.postMessage({ type: 'FROM_PAGE_SCRIPT_ERROR', token: '${token}', text: message, error: error }, '*');
  };
  ` + source + `
    window.result = window.result || null;
    window.postMessage({ type: 'FROM_PAGE_SCRIPT', token: '${token}', text: window.result }, '*');
    `;

  return executeScript(source, token);
}


function addScriptToPage(source) {
  const script = document.createElement('script');
  script.textContent = source;
  document.body.appendChild(script);
  document.body.removeChild(script);
}


addScriptToPage(`
function waitForElement(selector, timeout = 120000) {
  return new Promise((resolve, reject) => {
      let el = document.querySelector(selector);
      
      if (el) { 
          resolve(el);
          return;
      }
      
      const observer = new MutationObserver((mutationRecords, observer) => {
          // Query for element again each time the DOM changes
          el = document.querySelector(selector);
          
          if (el) {
              resolve(el);
              // Once we have resolved we don't need the observer anymore
              observer.disconnect();
          }
      });
      
      observer.observe(document.body, { 
          childList: true, 
          subtree: true 
      });

      // Set a timeout to reject promise after 5s
      setTimeout(() => {
          observer.disconnect();
          reject(new Error('Timeout waiting for element'));
      }, timeout);
  });
}


function getCssPath(element) {
  if (!(element instanceof Element)) 
      return;
  let path = [];
  while (element.nodeType === Node.ELEMENT_NODE) {
      let selector = element.nodeName.toLowerCase();
      if (element.id) {
          selector += '#' + element.id;
          path.unshift(selector);
          break;
      } else {
          let sibling = element;
          let siblingSelector = selector;
          let index = 1;
          while (sibling = sibling.previousElementSibling) {
              if (sibling.nodeName.toLowerCase() === selector) {
                  index++;
              }
          }
          if (index > 1) {
              selector += ':nth-child(' + index + ')';
          }
      }
      path.unshift(selector);
      element = element.parentNode;
  }
  return path.join(' > ');
}

`);
