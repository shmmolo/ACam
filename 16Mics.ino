#include <Audio.h>
#include <Wire.h>
#include <SPI.h>

// GUItool: begin automatically generated code
AudioInputTDM            tdm1;           //xy=172,228
AudioInputTDM2           tdm2_1;

// 16 queues (2 slots per mic × 8 mics)
// tdm1
AudioRecordQueue         queue1;  AudioRecordQueue queue2;
AudioRecordQueue         queue3;  AudioRecordQueue queue4;
AudioRecordQueue         queue5;  AudioRecordQueue queue6;
AudioRecordQueue         queue7;  AudioRecordQueue queue8;
AudioRecordQueue         queue9;  AudioRecordQueue queue10;
AudioRecordQueue         queue11; AudioRecordQueue queue12;
AudioRecordQueue         queue13; AudioRecordQueue queue14;
AudioRecordQueue         queue15; AudioRecordQueue queue16;

// tdm2_1
AudioRecordQueue         queue17;  AudioRecordQueue queue18;
AudioRecordQueue         queue19;  AudioRecordQueue queue20;
AudioRecordQueue         queue21;  AudioRecordQueue queue22;
AudioRecordQueue         queue23;  AudioRecordQueue queue24;
AudioRecordQueue         queue25;  AudioRecordQueue queue26;
AudioRecordQueue         queue27;  AudioRecordQueue queue28;
AudioRecordQueue         queue29;  AudioRecordQueue queue30;
AudioRecordQueue         queue31;  AudioRecordQueue queue32;

// tdm1 → slots 0–15
AudioConnection          patchCord1(tdm1, 0, queue1, 0);
AudioConnection          patchCord2(tdm1, 1, queue2, 0);
AudioConnection          patchCord3(tdm1, 2, queue3, 0);
AudioConnection          patchCord4(tdm1, 3, queue4, 0);
AudioConnection          patchCord5(tdm1, 4, queue5, 0);
AudioConnection          patchCord6(tdm1, 5, queue6, 0);
AudioConnection          patchCord7(tdm1, 6, queue7, 0);
AudioConnection          patchCord8(tdm1, 7, queue8, 0);
AudioConnection          patchCord9(tdm1, 8, queue9, 0);
AudioConnection          patchCord10(tdm1, 9, queue10, 0);
AudioConnection          patchCord11(tdm1, 10, queue11, 0);
AudioConnection          patchCord12(tdm1, 11, queue12, 0);
AudioConnection          patchCord13(tdm1, 12, queue13, 0);
AudioConnection          patchCord14(tdm1, 13, queue14, 0);
AudioConnection          patchCord15(tdm1, 14, queue15, 0);
AudioConnection          patchCord16(tdm1, 15, queue16, 0);

// tdm2 → slots 0–15
AudioConnection          patchCord17(tdm2_1, 0, queue17, 0);
AudioConnection          patchCord18(tdm2_1, 1, queue18, 0);
AudioConnection          patchCord19(tdm2_1, 2, queue19, 0);
AudioConnection          patchCord20(tdm2_1, 3, queue20, 0);
AudioConnection          patchCord21(tdm2_1, 4, queue21, 0);
AudioConnection          patchCord22(tdm2_1, 5, queue22, 0);
AudioConnection          patchCord23(tdm2_1, 6, queue23, 0);
AudioConnection          patchCord24(tdm2_1, 7, queue24, 0);
AudioConnection          patchCord25(tdm2_1, 8, queue25, 0);
AudioConnection          patchCord26(tdm2_1, 9, queue26, 0);
AudioConnection          patchCord27(tdm2_1, 10, queue27, 0);
AudioConnection          patchCord28(tdm2_1, 11, queue28, 0);
AudioConnection          patchCord29(tdm2_1, 12, queue29, 0);
AudioConnection          patchCord30(tdm2_1, 13, queue30, 0);
AudioConnection          patchCord31(tdm2_1, 14, queue31, 0);
AudioConnection          patchCord32(tdm2_1, 15, queue32, 0);


// Helper: reconstruct 16-bit signed sample from two 16-bit TDM slots
int32_t reconstructSample(int16_t high, int16_t low) {
uint32_t word = ((uint32_t)(uint16_t)high << 8)
              | ((uint32_t)(uint16_t)low  >> 8);
// now word’s valid 24-bits sit in 23:0
return (int32_t)(word << 8) >> 8;    // sign-extend from 24→32

// int32_t sample = (int32_t)high << 8;
// sample |= (uint16_t)low >> 8;
// return sample
}

static const int SUBBLOCK = 16;      // send blocks of 16 samples
static const int MICS = 16;      // number of channels
static const int SLOT_COUNT = 2 * MICS; // each mic uses 2 TDM slots → 18

// Array of pointers so we can loop over all 16 queues
AudioRecordQueue* queues[SLOT_COUNT] = // creating array to simplify iteration
{
  &queue1, &queue2, &queue3, &queue4,
  &queue5, &queue6, &queue7, &queue8,
  &queue9, &queue10,&queue11,&queue12,
  &queue13,&queue14,&queue15,&queue16,
  &queue17, &queue18, &queue19, &queue20,
  &queue21, &queue22, &queue23, &queue24,
  &queue25, &queue26,&queue27,&queue28,
  &queue29,&queue30,&queue31,&queue32,
};

void setup() {
  Serial.begin(2000000);
  AudioMemory(64); // defines how many “blocks” the Teensy Audio library can ever allocate for all its internal queues, mixers... 
                   // since i am already using 16 blocks for data there are also buffers, queues and so on... so as optimal number AudioMemoryUsageMax() + 10
  // start all 16 queues
  // instead of writing queue1.begin() I write the following loop
  for (int q = 0; q < SLOT_COUNT; q++) {
    queues[q]->begin();
  }
}

void loop() {
  // wait until every queue has data
  for (int q = 0; q < SLOT_COUNT; q++) {
    if (queues[q]->available() <= 0) return; // if queue1.available() < 0, do nothing
  }
  // read all buffers & check for null
  int16_t* buffers[SLOT_COUNT];
  for (int q = 0; q < SLOT_COUNT; q++) {
    buffers[q] = queues[q]->readBuffer(); // reading all buffers
    if (!buffers[q]) {
      for (int i = 0; i < SLOT_COUNT; i++) queues[i]->freeBuffer();
      return;
    }
  }

// 3) for each 16-sample sub-block inside that 128-sample buffer:
//    reconstruct and send immediately
static int32_t block[ MICS * SUBBLOCK ];
for (int offset = 0; offset < 128; offset += SUBBLOCK) {
  // process a SUBBLOCK×MICS chunk
  for (int i = 0; i < SUBBLOCK; i++) {
    // for each mic, reconstruct, store, and print
    for (int mic = 0; mic < MICS; mic++) {
      int32_t sample = reconstructSample(
        buffers[2*mic    ][ offset + i ],
        buffers[2*mic + 1][ offset + i ]
      );
      block[i * MICS + mic] = sample;

      Serial.print(sample);        // print value
      if (mic < MICS - 1)          // comma except after last mic
        Serial.print(',');
    }
    Serial.println();              // end of one sample’s line
  }
  // when you’re ready to stream the raw block:
  // Only write if enough space in serial buffer
  //Serial.write((uint8_t*)block, sizeof(block));

}

  // free all buffers
  for (int q = 0; q < SLOT_COUNT; q++) {
    queues[q]->freeBuffer(); // free buffers for next iteration
  }
}

/* 
unsigned long lastReport = 0;
const unsigned long reportInterval = 5000;  // 5 seconds

  // every reportInterval ms, print peak AudioMemory usage
 
    if (millis() - lastReport > reportInterval) {
    lastReport = millis();
    Serial.print("Peak audio blocks used: ");
    Serial.println(AudioMemoryUsageMax()); // 
  }
*/