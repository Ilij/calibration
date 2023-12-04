var pc = null;
let datachannel;

function negotiate() {
    pc.addTransceiver('video', {direction: 'recvonly'});
    return pc.createOffer({iceRestart:true})
        .then(function(offer) {
            return pc.setLocalDescription(offer);
         })
         .then(function() {
        // wait for ICE gathering to complete
        return new Promise(function(resolve) {
            if (pc.iceGatheringState === 'complete') {
                resolve();
            } else {
                function checkState() {
                    if (pc.iceGatheringState === 'complete') {
                        pc.removeEventListener('icegatheringstatechange', checkState);
                        resolve();
                    }
                }
                pc.addEventListener('icegatheringstatechange', checkState);
            }
        });
    }).then(function() {
        var offer = pc.localDescription;
        return fetch('/offer', {
            body: JSON.stringify({
                sdp: offer.sdp,
                type: offer.type,
            }),
            headers: {
                'Content-Type': 'application/json'
            },
            method: 'POST'
        });
    }).then(function(response) {
        return response.json();
    }).then(function(answer) {
        pc.setRemoteDescription(answer);
    }).catch(function(e) {
        alert(e);
    });
}


function connect(dataCallBack) {
    var config = {
        sdpSemantics: 'unified-plan'
    };

    pc = new RTCPeerConnection(config);

    let v = document.getElementById('video');

    // connect audio / video
    pc.addEventListener('track', function(evt) {
        if (evt.track.kind == 'video') {
            v.srcObject = evt.streams[0];
        } 
    });

    // pc.ondatachannel = function(event){
    //     datachannel = event.channel;

    //     datachannel.onopen = function() {
    //         console.log('datachannel open by server');
    //     };

    //     datachannel.onclose = function() {
    //         console.log('datachannel close');
    //     };

    //     datachannel.onerror = function(error){
    //         console.log('Error in datachannel:', error);
    //     }

    //     datachannel.onmessage = function(event){
    //         console.log('datachannel message:', event.data);
    //         dataCallBack(JSON.parse(event.data));
    //     };
    // }

    datachannel = pc.createDataChannel("web_client")
    datachannel.onmessage = function(event){
        try{
            dataCallBack(JSON.parse(event.data));
        }
        catch{
        }
        datachannel.send("ok");
    };

    datachannel.onopen = function() {
        datachannel.send('client ping')
        console.log('datachannel open by client');
    };

    datachannel.onclose = function() {
        console.log('client datachannel close');
    };

    negotiate();
}


function stop() {
    document.getElementById('stop').style.display = 'none';
    document.getElementById('start').style.display = 'inline-block';
    // close peer connection
    setTimeout(function() {
        pc.close();
    }, 500);
}

// // Tone generation
// //
// // determine if Web Audio API is available
// // (`contextClass` will return `false` if
// // the API is not supported).
// const context = new (window.AudioContext || window.webkitAudioContext)();

// // VCO #1
// // Create an oscillator using the API:
// const vco1 = context.createOscillator();
// // Set the waveform for our new VCO:
// vco1.type = "triangle"; // sine | square | sawtooth | triangle
// // Set the starting frequency for the VCO
// vco1.frequency.value = 440.0; // 440.00Hz = "A", the standard note all orchestras tune to.

// // VCA
// // This is a gain (volume) node that
// // will control the volume of the note.
// const vca = context.createGain();
// vca.gain.value = 0;

// // VCO#1 VOLUME
// // Gain node for VCO#1
// const vco1vol = context.createGain();
// vco1vol.gain.value = 1;

// // MASTER VCA
// // This is our overall volume control
// // When we trigger a note, the normal
// // VCA goes from 0 to full. Having a
// // master volume control allows us to
// // set the global volume without
// // affecting the notes' on/off function.
// const master = context.createGain();
// master.gain.value = 0.5;

// // DELAY
// var delay = context.createDelay();
// delay.delayTime.value = 0;
// var delay_feedback = context.createGain();
// delay_feedback.gain.value = 0.2;
// var delay_filter = context.createBiquadFilter();
// delay_filter.frequency.value = 2000;

// // CONNECTIONS
// // Here we link all our nodes
// // together. The final setting
// // of `context.destination`
// // pipes the resulting sounds
// // to our audio output, so we
// // can hear it.
// vco1.connect(vco1vol);
// vco1vol.connect(vca);

// // No effects:
// vca.connect(master);

// vca.connect(delay);
// delay.connect(delay_feedback);
// delay_feedback.connect(delay_filter);
// delay_filter.connect(delay);
// delay.connect(master);

// master.connect(context.destination);

// const controlPad = document.querySelector("#controlPad");
// const controlPadMarker = document.querySelector("#controlPadMarker");

// const state = {
//     running: false,
//     volumeInput: 0,
//     pitchInput: 0,
//     noteOn: false,
//     notePersist: false,
// };

// const getPosition = (element) => ({
//     top: window.scrollY + element.getBoundingClientRect().top,
//     left: window.scrollX + element.getBoundingClientRect().left,
// });

// /**
//  * ------------------
//  * CONTROL PAD EVENTS
//  * ------------------
//  */
// controlPad.addEventListener("mousedown", (e) => {
//     if (!state.running) {
//         // Get the VCO running
//         vco1.start(0);
//         state.running = true;
//     }
//     state.noteOn = true;
//     const position = getPosition(controlPad);
//     const rawVolInput = e.pageY - position.top;
//     const rawPitchInput = e.pageX - position.left;
//     setNote(rawVolInput, rawPitchInput);
// });

// controlPad.addEventListener("mouseleave", (e) => {
//     if (state.noteOn) {
//         state.notePersist = true;
//     } else {
//         state.notePersist = false;
//     }
//     state.noteOn = false;
//     vca.gain.value = 0;
// });

// controlPad.addEventListener("mouseenter", (e) => {
//     if (state.notePersist) {
//         state.noteOn = true;
//         const position = getPosition(controlPad);
//         var rawVolInput = e.pageY - position.top;
//         var rawPitchInput = e.pageX - position.left;
//         setNote(rawVolInput, rawPitchInput);
//     }
// });

// document.addEventListener("mouseup", (e) => {
//     // console.log('mouseup');
//     state.noteOn = false;
//     state.notePersist = false;
//     vca.gain.value = 0;
//     controlPadMarker.classList.remove("active");
// });

// controlPad.addEventListener("mousemove", (e) => {
//     const position = getPosition(controlPad);
//     const rawVolInput = e.pageY - position.top;
//     const rawPitchInput = e.pageX - position.left;
//     if (state.noteOn) {
//         setNote(rawVolInput, rawPitchInput);
//     }
//     setMarker(rawVolInput, rawPitchInput);
// });

// // Set Marker Positon
// function setMarker(x, y) {
//     controlPadMarker.style.top = x + "px";
//     controlPadMarker.style.left = y + "px";
// }

// function setNote(volume, pitch) {
//     state.volumeInput = parseNoteValue(volume);
//     state.pitchInput = parsePitchValue(pitch);
//     vca.gain.value = state.volumeInput;
//     vco1.frequency.value = state.pitchInput;
// }

// // Parse note value.
// // -----------------
// // Make sure we're using a value
// // between 0.00 and 1.00 for volume.
// function parseNoteValue(input) {
//     var output = input / 300;
//     return (1 - output).toFixed(2);
// }

// // Parse pitch value.
// // ------------------
// // Make sure we're using a value
// // between 200.00 and 800.00 for pitch.
// function parsePitchValue(input) {
//     var output = input * 2;
//     var output = input * 10;
//     // output = output + 200;
//     return output.toFixed(2);
// }

// // Get Wave-Type Selection
// var waveSelectorRadio = document.waveTypeForm.waveSelector;
// for (var i = 0; i < waveSelectorRadio.length; i++) {
//     waveSelectorRadio[i].onclick = function () {
//         var rawWave = this.value;
//         var waveType = parseWave(rawWave);
//         setWave(waveType);
//     };
// }

// // Turn wave-type int into string
// function parseWave(int) {
//     // Make sure the input is a string
//     string = int.toString();
//     var waveType = false;
//     switch (string) {
//         case "1":
//             waveType = "sine";
//             break;
//         case "2":
//             waveType = "square";
//             break;
//         case "3":
//             waveType = "triangle";
//             break;
//         case "4":
//             waveType = "sawtooth";
//             break;
//     }
//     return waveType;
// }

// // Set the wave type of an oscillator
// function setWave(waveType) {
//     vco1.type = waveType;
// }
