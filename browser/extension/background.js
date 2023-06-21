// background.js


async function loadUrlInTab(tabId, url) {
  try {
    let updated = await browser.tabs.update(tabId, { url: url });
    if (updated.url === url) {
      return {result: true, message: ''};
    } else {
      throw new Error(`Failed to load URL in tab: ${url}`);
    }
  } catch (err) {
    console.error('Failed to update tab:', err);
    return {result: false, message: err.message};
  }
}

async function openNewTab(url) {
  try {
    console.log('Opening new tab:', url);
    const tab = await browser.tabs.create({ url: url });
    return {result: tab.id, message: ''};
  } catch (error) {
    console.error('Error opening new tab:', error);
    return {result: false, message: error.message};
  }
}


async function listTabs() {
  try {
    const tabs = await browser.tabs.query({});
    const tabList = tabs.map((tab) => ({
      id: tab.id, 
      url: tab.url,
      title: tab.title 
    }));
    return tabList;
  } catch (err) {
    console.error('Failed to list tabs:', err);
  }
}


async function closeTabByUrl(url) {
  try {
    const tabs = await browser.tabs.query({ url: url });
    if (tabs.length) {
      await Promise.all(tabs.map((tab) => browser.tabs.remove(tab.id)));
      return true;
    }
  } catch (error) {
    console.error('Error closing tab by URL:', error);
    return false;
  }
}


async function closeTabById(tabId) {
  try {
    const parsedTabId = parseInt(tabId, 10);
    if (isNaN(parsedTabId)) {
      throw new Error('InvalidTabIdError');
    }
    await browser.tabs.remove(parsedTabId);
    return {result: true, message: ''};
  } catch (error) {
    console.error(`Error closing tab by ID: ${error.message}`);

    //if (error.message.startsWith('Invalid tab ID:')) {
      // Handle invalid tab ID error specifically
    //  return {result: false, message: "InvalidTabIdError"};
    //}

    return {result: false, message: error.message};
  }
}


async function getTabHTML(tabId) {
  try {
    const html = await browser.tabs.sendMessage(
          parseInt(tabId, 10), 
          { action: 'getHTML' }
    );
    return html;
  } catch (error) {
    console.error('Error getting HTML from content script:', error);
    return false;
  }
}


function waitForElement_bg(tabId, selector, timeout) {
  console.log('waitForElement_bg() called in background.js: ' + tabId + ' ' + selector + ' ' + timeout);

  return new Promise((resolve, reject) => {
        resolve(sendMessage(tabId, selector, timeout));
  });
}

function sendMessage(tabId, selector, timeout) {
  return new Promise((resolve, reject) => {
    let startTime = Date.now();
    
    async function retrySendMessage() {
      console.log("background script is sending the message...");
      
      try {
        const result = await browser.tabs.sendMessage(
          parseInt(tabId, 10),
          { action: 'waitForElement', selector: selector, timeout: timeout }
        );
        console.log("waitForElement_bg result: " + result);
        resolve({'result': 'success', message: 'OK'});
      } catch (error) {
        let elapsedTime = Date.now() - startTime;
        
        if (elapsedTime < timeout) {
          console.log('Retrying...');
          setTimeout(retrySendMessage, 1000);  // Retry after 1 second
        } else {
          console.error('Error waiting for element in content script:', error);
          resolve({'result': 'error', 'message': error.message});
        }
      }
    }

    // Start the first attempt
    retrySendMessage();
  });
}


function injectScript_bg(tabId, source) {
  return new Promise((resolve, reject) => {
    async function retryInjectScript() {
      console.log("background script is injecting the script...");
      
      try {
        const result = await browser.tabs.sendMessage(
          parseInt(tabId, 10),
          { action: 'injectScript', source: source }
        );
        console.log("injectScript_bg result: " + result);
        resolve({'status': 'success', message: 'OK', 'result': result});
      } catch (error) {
          console.error('Error injecting script into content script:', error);
          resolve({'status': 'success', 'message': 'OK', 'result': error.message});
      }
    }

    // Start the first attempt
    retryInjectScript();
  });
}


function setupWebSocketConnection() {
  // Create WebSocket connection using socket.io
  const webSocketURL = 'https://0.0.0.0/';
  const socket = io(webSocketURL);
  console.log("trying connection");

  socket.on('connect', () => {
    console.log('Socket.IO connection established');
  });

  socket.on('message', (data) => {
      console.log(data['data']);
      console.log('Socket.IO message received:', data);
  });

  socket.on('tabs_list', async (data) => {
    console.log("tabs_list request received");
    try {
      const tabList = await listTabs();
      socket.emit('message', { result: tabList, request_id: data['request_id'] });
    } catch (error) {
      console.error('Error listing tabs:', error);
      socket.emit('message', { result: false, message: error.message, request_id: data['request_id'] });
    }
  });

  socket.on('load_url_in_tab', async (data) => {
    console.log("load_url_in_tab request received");
    try {
      const result = await loadUrlInTab(data['tab_id'], data['url']);
      socket.emit('message', { result: result.result,
          message: result.message,
          request_id: data['request_id'] });
    } catch (error) {
      socket.emit('message', { 
        result: false, 
        message: error.message, 
        request_id: data['request_id']
      })
    };
  });
  
  socket.on('close_tab_by_url', async (data) => {
    const result = await closeTabByUrl(data['url']);
    socket.emit('message', { result: result, request_id: data['request_id'] });
  });


  socket.on('close_tab_by_id', async (data) => {
    const result = await closeTabById(data['tab_id']);
    let message = '';
    if (!result.result) {
        message = result.message;
    }
    socket.emit('message', { result: result.result, 
        message: message, request_id: data['request_id'] });
});


  socket.on('open_new_tab', async (data) => {
    const result = await openNewTab(data['url']);
    socket.emit('message', { result: result['result'], 
        message: result['message'], 
        request_id: data['request_id'] });
  });

  socket.on('execute_script', async (data) => {
    const result = await browser.tabs.executeScript(data['tab_id'], { code: data['code'] });
    socket.emit('message', { result: result, request_id: data['request_id'] });
  });

  async function postResult(result, requestId) {
    console.log(result);
    fetch('https://0.0.0.0/response', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ result: result, request_id: requestId })
    }).then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    }).then(data => {
        console.log('Success:', data);
    }).catch(error => {
        console.error('Error:', error);
    });
}

socket.on('wait_for_element', async (data) => {
  console.log("wait_for_element message received in background.js");
  const result = await waitForElement_bg(data['tab_id'], 
      data['selector'],
      data['timeout']);
  postResult(result, data['request_id']);
});

socket.on('inject_script', async (data) => {
    const result = await injectScript_bg(data['tab_id'], data['code']);
    postResult(result, data['request_id']);
});

socket.on('get_tab_html', async (data) => {
    const result = await getTabHTML(data['tab_id']);
    postResult(result, data['request_id']);
});


  socket.on('disconnect', () => {
    console.log('Socket.IO connection closed');
  });

  socket.on('error', (error) => {
    console.error('Socket.IO error:', error);
  });
}

async function loadLibraries() {
  const socketIoLib = 'https://localhost/static/socket.io.js';
  await import(socketIoLib);
}

loadLibraries().then(() => {
  console.log("test");
  setupWebSocketConnection();
});