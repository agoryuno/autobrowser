def extract_text(element:str = "document.body",
                 onlyVisible:bool = True,
                 flat:bool = False):
    fstr = f"""function extractInnerText(
            element={element}, 
            onlyVisible={"true" if onlyVisible else "false"}, 
            flat={"true" if flat else "false"}
            ) {{
    let resultObj = {{}};

    let allElements = element.querySelectorAll('*');

    allElements.forEach(el => {{
        // Check if the element is visible
        if (onlyVisible) {{
            let style = window.getComputedStyle(el);
            if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {{
                return;
            }}
        }}

        // If element is an iframe, recursively call extractInnerText
        if (el.tagName.toLowerCase() === 'iframe') {{
            try {{
                // Accessing contentDocument may throw a security exception in case of cross-origin iframes
                let iframeContent = el.contentDocument || el.contentWindow.document;
                let iframeResult = extractInnerText(iframeContent.body, onlyVisible, flat);

                Object.keys(iframeResult).forEach(key => {{
                    if (resultObj[key]) {{
                        resultObj[key].push(...iframeResult[key]);
                    }} else {{
                        resultObj[key] = iframeResult[key];
                    }}
                }});
            }} catch (e) {{
                console.log('Skipping cross-origin iframe');
            }}
            return;
        }}

        // Exclude <script> and <style> elements
        if (el.tagName.toLowerCase() === 'script' || el.tagName.toLowerCase() === 'style') {{
            return;
        }}

        // Exclude elements that have child elements
        if (el.children.length > 0) {{
            return;
        }}

        // Add the text content to the result object if it's not empty or just whitespace
        let text = el.textContent.trim();
        if (text) {{
            let parentHTML = el.parentElement.outerHTML;
            if (resultObj[parentHTML]) {{
                resultObj[parentHTML].push(text);
            }} else {{
                resultObj[parentHTML] = [text];
            }}
        }}
    }});

    let result = Object.values(resultObj);

    // If 'flat' argument is true, flatten the array before returning
    if (flat) {{
        result = result.flat();
    }}

    return result;
}}

window.result = extractInnerText();

"""
    return fstr



def extract_text_map(element:str = "document.body",
                   onlyVisible:bool = True,
                   flat:bool = False):
    fstr = f"""function getCssPath(el, root) {{
    let path = [];
    while (el && el.nodeType === Node.ELEMENT_NODE && el !== root.parentNode) {{
        let selector = el.nodeName.toLowerCase();
        if (el.id) {{
            selector += '#' + el.id;
        }} else {{
            let sibling = el;
            let siblingSelectors = [];
            while (sibling !== null && sibling.nodeType === Node.ELEMENT_NODE) {{
                siblingSelectors.unshift(sibling.nodeName.toLowerCase());
                sibling = sibling.previousElementSibling;
            }}
            if (siblingSelectors.length !== 0) {{
                selector += ":nth-child(" + (siblingSelectors.length) + ")";
            }}
        }}
        path.unshift(selector);
        el = el.parentNode;
    }}
    return path.join(" > ");
}}

function extractInnerText(
        element={element}, 
        onlyVisible={"true" if onlyVisible else "false"}, 
        flat={"true" if flat else "false"}
    ) {{
    let resultObj = {{}};

    let allElements = element.querySelectorAll('*');

    allElements.forEach(el => {{
        // Check if the element is visible
        if (onlyVisible) {{
            let style = window.getComputedStyle(el);
            if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {{
                return;
            }}
        }}

        // If element is an iframe, recursively call extractInnerText
        if (el.tagName.toLowerCase() === 'iframe') {{
            try {{
                let iframeContent = el.contentDocument || el.contentWindow.document;
                let iframeResult = extractInnerText(iframeContent.body, onlyVisible, flat);

                Object.keys(iframeResult).forEach(key => {{
                    if (resultObj[key]) {{
                        Object.assign(resultObj[key], iframeResult[key]);
                    }} else {{
                        resultObj[key] = iframeResult[key];
                    }}
                }});
            }} catch (e) {{
                console.log('Skipping cross-origin iframe');
            }}
            return;
        }}

        // Exclude <script> and <style> elements
        if (el.tagName.toLowerCase() === 'script' || el.tagName.toLowerCase() === 'style') {{
            return;
        }}

        // Exclude elements that have child elements
        if (el.children.length > 0) {{
            return;
        }}

        // Add the text content to the result object if it's not empty or just whitespace
        let text = el.textContent.trim();
        if (text) {{
            let parentSelector = getCssPath(el.parentElement, element);
            let childSelector = getCssPath(el, element);

            // Remove the parent's path from the child's path to create a relative path
            childSelector = childSelector.replace(parentSelector + ' > ', '');

            if (resultObj[parentSelector]) {{
                resultObj[parentSelector][childSelector] = text;
            }} else {{
                resultObj[parentSelector] = {{}};
                resultObj[parentSelector][childSelector] = text;
            }}
        }}
    }});

    // If 'flat' argument is true, flatten the object before returning
    if (flat) {{
        let result = {{}};
        for (let parent in resultObj) {{
            for (let child in resultObj[parent]) {{
                result[`${{parent}} > ${{child}}`] = resultObj[parent][child];
            }}
        }}
        return result;
    }}

    return resultObj;
}}

window.result = extractInnerText();
"""
    return fstr