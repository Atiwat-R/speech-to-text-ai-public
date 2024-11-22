"use client"

import React, { useState, useEffect } from 'react';

const TextDisplay = ({ path }) => {
    const [text, setText] = useState('');

    const updateMilisec = 10


    const fetchText = async () => {
        try {
            const response = await fetch(path);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

  
            const data = await response.json();

            console.log(data)
            setText(data);
        } catch (error) {
            console.error('Error fetching the text file:', error);
        }
    };

    useEffect(() => {
        fetchText();
        const interval = setInterval(fetchText, updateMilisec);
        return () => clearInterval(interval); // Cleanup on unmount
    }, []);

    return (
        <div style={{ fontFamily: 'monospace' }}>
            {text}
        </div>
    );
};

export default TextDisplay;
