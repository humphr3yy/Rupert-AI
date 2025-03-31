# Rupert's British Voice Configuration Guide

This document provides detailed information about Rupert's British voice settings and how to customize them.

## Voice Overview

Rupert is designed to speak with a sophisticated British accent, reflecting his philosophical persona. The voice is specifically tuned to convey the character's thoughtful, erudite nature through carefully selected voice parameters.

## Available TTS Engines

Rupert can use any of the following Text-to-Speech engines:

### 1. Piper TTS (Recommended)

Piper provides the highest quality voice with the most natural-sounding British accent. It uses a neural voice model that can be fully customized.

**Default Settings:**
- **Model**: en_US-lessac-medium (Modified for British accent)
- **Speed**: 1.1 (Slightly slower, adds gravitas and sophistication)
- **Variation**: 0.7 (Higher variation creates more expressive speech patterns)
- **Randomness**: 0.75 (Adds natural cadence and prevents monotony)

### 2. Google Text-to-Speech (Alternative)

This option uses the built-in pyttsx3 library with a British English voice profile.

**Default Settings:**
- **Voice ID**: British English male voice
- **Rate**: 150 (Standard speaking rate)
- **Volume**: 1.0 (Standard volume)

### 3. gTTS (Online alternative)

Google's online TTS service with British English accent selection.

**Default Settings:**
- **Language**: en-gb (British English)
- **Slow**: False (Normal speaking rate)

## Customizing Voice Parameters

### Via Environment Variables

You can customize the TTS settings by modifying the following variables in your `.env` file:

```
# TTS Engine Selection
TTS_ENGINE=piper  # Options: piper, google, gtts

# Language Selection
TTS_LANGUAGE=en-GB

# Piper Voice Parameters
PIPER_SPEED=1.1
PIPER_VARIATION=0.7
PIPER_RANDOMNESS=0.75
```

### Via Code

For more advanced customization, you can modify the voice parameters directly in `tts.py`:

```python
# Example: Adjusting Piper TTS parameters
piper_tts = PiperTTS()
piper_tts.set_voice_parameters(
    speed=1.1,        # Range: 0.5-2.0 (higher = slower)
    variation=0.7,    # Range: 0.1-1.0 (higher = more variation)
    randomness=0.75   # Range: 0.1-1.0 (higher = more randomness)
)
```

## Parameter Explanations

### Speed (1.1)

The speed parameter controls how quickly Rupert speaks. A value of 1.0 is the default speed, while higher values make the speech slower.

- **1.1** - Slightly slower than normal, giving Rupert's voice a more thoughtful, measured quality
- **< 1.0** - Faster speech, may sound rushed or less dignified
- **> 1.2** - Very slow speech, may sound too ponderous

### Variation (0.7)

The variation parameter controls the prosodic variety in Rupert's speech - essentially how much his pitch and tone change during speaking.

- **0.7** - High variation creates more expressive, engaging speech with natural emphasis
- **< 0.5** - Lower variation sounds more monotone and robotic
- **> 0.8** - Very high variation can sound overly dramatic

### Randomness (0.75)

The randomness parameter affects the natural variations in phoneme pronunciation, creating the subtle differences that make human speech sound natural rather than synthetic.

- **0.75** - Provides natural-sounding speech with the appropriate British speech patterns
- **< 0.5** - More consistent but potentially more artificial-sounding
- **> 0.9** - Might introduce too much unpredictability in pronunciation

## Achieving the British Philosophical Character

The combination of these specific parameters helps create Rupert's distinct voice characteristics:

1. **Slightly slower speed** (1.1) gives weight to his philosophical insights
2. **Higher variation** (0.7) reflects his emotional engagement with complex topics
3. **Balanced randomness** (0.75) provides the natural cadence of educated British speech

Together, these settings create a voice that conveys erudition, thoughtfulness, and the measured delivery of someone accustomed to deep thinking and careful expression.

## Testing Voice Changes

After making changes to voice parameters, you can test them using the `run_bot.py` script without needing to connect to Discord:

```bash
python test_tts.py "This is a test of Rupert's sophisticated British voice. How does it sound?"
```

This will generate an audio file with the test message using your current TTS settings.