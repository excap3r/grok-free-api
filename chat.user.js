// ==UserScript==
// @name         Grok Chat API
// @namespace    http://tampermonkey.net/
// @version      0.2
// @description  Interface with Grok chat through a local server
// @author       You
// @match        https://grok.com/*
// @grant        GM_xmlhttpRequest
// ==/UserScript==

(function() {
    'use strict';

    const API_BASE = 'http://localhost:5001/api/v1';
    const RETRY_DELAY = 5000;
    const MAX_RETRIES = 10;
    let lastProcessedMessage = null;

    function getChatElements() {
        const textarea = document.querySelector('textarea');
        const submitButton = document.querySelector('button[type="submit"]');
        return { textarea, submitButton };
    }

    function makeRequest(endpoint, method = 'GET', data = null) {
        return new Promise((resolve, reject) => {
            GM_xmlhttpRequest({
                method: method,
                url: `${API_BASE}${endpoint}`,
                data: data ? JSON.stringify(data) : null,
                headers: {
                    'Content-Type': 'application/json',
                    'Origin': 'https://grok.com',
                    'Accept': 'application/json'
                },
                anonymous: true,
                onload: function(response) {
                    try {
                        const result = JSON.parse(response.responseText);
                        if (response.status >= 200 && response.status < 300) {
                            resolve(result);
                        } else {
                            reject(result.error || 'Request failed');
                        }
                    } catch (e) {
                        reject('Invalid response format');
                    }
                },
                onerror: function(error) {
                    reject(error);
                }
            });
        });
    }

    function sendMessage(message) {
        const { textarea, submitButton } = getChatElements();
        if (!textarea || !submitButton) {
            console.error('Chat elements not found');
            return false;
        }

        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
        nativeInputValueSetter.call(textarea, message);

        const reactFocusEvent = new FocusEvent('focus', { bubbles: true, composed: true });
        reactFocusEvent.simulated = true;
        textarea.dispatchEvent(reactFocusEvent);

        const compositionStartEvent = new CompositionEvent('compositionstart', { bubbles: true });
        const compositionEndEvent = new CompositionEvent('compositionend', { bubbles: true, data: message });
        textarea.dispatchEvent(compositionStartEvent);
        textarea.dispatchEvent(compositionEndEvent);

        const inputEvent = new InputEvent('input', {
            bubbles: true,
            composed: true,
            inputType: 'insertText',
            data: message,
            isComposing: false
        });
        textarea.dispatchEvent(inputEvent);

        const changeEvent = new Event('change', { bubbles: true });
        changeEvent.simulated = true;
        textarea.dispatchEvent(changeEvent);

        textarea._valueTracker?.setValue('');
        textarea.dispatchEvent(new Event('input', { bubbles: true }));

        submitButton.click();
        return true;
    }

    async function getLastResponse(retries = 0) {
        try {
            const messages = document.querySelectorAll('.message-bubble');
            
            if (messages.length > 0) {
                const lastMessage = messages[messages.length - 1];
                const paragraphs = lastMessage.querySelectorAll('p');
                
                const parentDiv = lastMessage.closest('.relative.group');
                const isGenerating = parentDiv?.querySelector('.animate-spin') || 
                                    parentDiv?.querySelector('.typing-indicator') || 
                                    !parentDiv?.querySelector('button[aria-label="Share conversation"]');
                
                if (!isGenerating && paragraphs.length > 0) {
                    const messageText = Array.from(paragraphs)
                        .map(p => p.textContent.trim())
                        .filter(text => text.length > 0)
                        .join('\n');
                    
                    if (messageText.length > 0 && messageText !== lastProcessedMessage) {
                        lastProcessedMessage = messageText;
                        return messageText;
                    }
                }
            }
            
            if (retries < MAX_RETRIES) {
                await new Promise(resolve => setTimeout(resolve, RETRY_DELAY));
                return getLastResponse(retries + 1);
            }
            
            return null;
        } catch (error) {
            console.error('Error getting last response:', error);
            return null;
        }
    }

    async function processPendingMessage() {
        try {
            const result = await makeRequest('/chat/completions/latest');
            if (result.choices && result.choices.length > 0 && result.choices[0].message.content) {
                if (sendMessage(result.choices[0].message.content)) {
                    const response = await getLastResponse();
                    if (response) {
                        await makeRequest('/chat/completions', 'POST', { response });
                        await makeRequest('/messages/mark-processed', 'POST', { 
                            message: result.choices[0].message.content 
                        });
                    }
                }
            }
        } catch (error) {
            console.error('Error processing message:', error);
        }
    }

    function startMessageListener() {
        console.log('Starting message listener...');
        setInterval(processPendingMessage, 2000);
    }

    window.addEventListener('load', () => {
        console.log('Grok Chat API userscript loaded');
        startMessageListener();
    });
})();