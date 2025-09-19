#include <iostream>
#include <iomanip>
#include <fstream>
#include <unistd.h>
#include <cstdlib>
#include <cstdint>
#include <string>
#include <vector>
#include <map>
#include <stack>
#include <set>
#include <tuple>
#include <utility>
#include <bitset>
#include <cmath>

#include "femSN.hh"
#include "utility.hh"

#include "TFile.h"
#include "TTree.h"
#include "TObject.h"
#include "TString.h"

using namespace std;

enum class STATE : unsigned char {
	WAIT_EVENT_START,
	WAIT_FEM_HEADER,
	GET_ADC_WORD_CNT,
	GET_EVENT_NUM,
	GET_FRAME_NUM,
	GET_ADC_WORD_CHECKSUM,
	GET_SAMPLE_NUM,
	WAIT_CHANNEL_START,
	WAIT_ROI_START,
	WAIT_ROI_END,
	GET_FEM_HEADER_L,
	WAIT_FEM_HEADER_R,
	GET_EVENT_END
};

int main(int argc, char* argv[]) {
	
	string fin, dout;
	bool debug = false;
	bool progressBar = false;

	// read options from input command
  char option;
  while ((option = getopt(argc, argv, "i:o:pdh")) != -1) {
    switch (option) {
      case 'i':
        fin = optarg;
        break;
      case 'o':
        dout = optarg;
        break;
      case 'p':
        progressBar = true;
        break;
      case 'd':
        debug = true;
        break;
      case 'h':
        cout << "USAGE: " << argv[0] << "\nOPTIONS\n"
                  << "-i : input file\n"
                  << "-o : output directory\n"
                  << "-p : display progress bar\n"
                  << "-d : debug mode\n";
        break;
      default:
        return 0;
    }
  }

	if (fin.empty()) {
    cout << "No input file" << endl;
    return 1;
  }
	else if (fin.find(".dat") == string::npos) {
    cout << "Input file must be a .dat file" << endl;
    return 1;
  }
  else if (dout.empty()) {
    cout << "No output directory" << endl;
    return 1;
  }

  ifstream fbin(fin, ios::in | ios::binary | ios::ate);

  if (!fbin.is_open()) {
    cout << fin << " can't be opened" << endl;
    return 1;
  }

	string fout = fin.substr((fin.find_last_of("/") + static_cast<int>((dout.back()=='/'))));
	string rootname = dout + fout.replace(fout.find(".dat"), 4, ".root");
	string logname = dout + fout.replace(fout.find(".root"), 5, ".log");

	ofstream flog;
  flog.open(logname);

	flog << "Input binary file: " << fin << "\n";
	flog << "Output root file: " << rootname << "\n";
	flog << "Output log file: " << logname << "\n";

	STATE state = STATE::WAIT_EVENT_START;

	unsigned int word32b;
	unsigned short word16b;

  map<unsigned short, femSN*> fems;
	channelSN *channel = new channelSN();
	unsigned short currFEMSlot, currROIADC;
	unsigned int currROIID, currROISampleNumCnt;
	bool roiStartMissCntInc;
	unsigned int currROIStartMissCnt, currROIEndMissCnt;
	unsigned int currADCWordCnt, currADCChecksum;

	TFile *froot = new TFile(rootname.c_str(), "RECREATE");
	TTree *event = new TTree("events", "events");

	unsigned int eventID = 0;
	bool eventEndMiss;
	bool allFEMHeaderMiss;
	event->Branch("eventID", &eventID, "eventID/i");
	event->Branch("eventEndMiss", &eventEndMiss, "eventEndMis/O");
	event->Branch("allFEMHeaderMiss", &allFEMHeaderMiss, "allFEMHeaderMiss/O");

	streamsize totalSize = fbin.tellg();
	fbin.seekg(0, ios::beg);
	streamsize bytesRead = 0;

  while (fbin) {
	  switch (state) {
		  case STATE::WAIT_EVENT_START: {
				fbin.read(reinterpret_cast<char*>(&word32b), sizeof(word32b));
				if (debug) cout << "WAIT_EVENT_START: " << "0x" << uppercase << hex << word32b << endl;
				if (word32b == EVENT_START) {
					if (eventID > 0) event->Fill();
					++eventID;
					eventEndMiss = true;
					allFEMHeaderMiss = true;
					for (auto& fem : fems) fem.second->setFEMSlot(0xFFFF);
					state = STATE::WAIT_FEM_HEADER;
				}
				else if (word32b == ((0xFFFF << 16) | EVENT_END)) {
					fbin.read(reinterpret_cast<char*>(&word16b), sizeof(word16b));
					if (word16b == 0xFFFF) {
						++eventID;
						eventEndMiss = true;
						allFEMHeaderMiss = true;
						for (auto& fem : fems) fem.second->setFEMSlot(0xFFFF);
						state = STATE::WAIT_FEM_HEADER;
					}
					else state = STATE::WAIT_FEM_HEADER_R;
				}
				else state = STATE::WAIT_EVENT_START;
				break;
			}
		  case STATE::WAIT_FEM_HEADER: {
				fbin.read(reinterpret_cast<char*>(&word32b), sizeof(word32b));
				if (debug) cout << "WAIT_FEM_HEADER: " << "0x" << uppercase << hex << word32b << endl;
				if (word32b == ((EVENT_END << 16) | 0x0)) {
					currROISampleNumCnt = 0;
					eventEndMiss = false;	
					state = STATE::WAIT_EVENT_START;
				}
				else if (((word32b & 0xFFFF) == FEM_HEADER) && ((word32b >> 28) == 0xF)) {
					currFEMSlot = (word32b >> 16) & 0x1F;
					if ((currFEMSlot > 2) && (currFEMSlot < 19)) {
						unsigned short femID = (word32b >> 21) & 0xF;
						bool test = static_cast<bool>(((word32b >> 25) & 0x1));
						bool overflow = static_cast<bool>(((word32b >> 26) & 0x1));
						bool full = static_cast<bool>(((word32b >> 27) & 0x1));
						if (fems.find(currFEMSlot) == fems.end()) {
							fems[currFEMSlot] = new femSN();
							event->Branch(Form("fem%d",currFEMSlot), "femSN", &fems[currFEMSlot]);
						}
						fems[currFEMSlot] = fems[currFEMSlot];
						fems[currFEMSlot]->setFEMSlot(currFEMSlot);
						fems[currFEMSlot]->setFEMID(femID);
						fems[currFEMSlot]->setTest(test);
						fems[currFEMSlot]->setOverflow(overflow);
						fems[currFEMSlot]->setFull(full);
						fems[currFEMSlot]->clearChannels();
						currADCWordCnt = 0;
						currADCChecksum = 0;
						allFEMHeaderMiss = false;
						state = STATE::GET_ADC_WORD_CNT;
					}
					else state = STATE::WAIT_FEM_HEADER_R;
				}
				else state = STATE::WAIT_FEM_HEADER_R;
				break;
			}
		  case STATE::GET_ADC_WORD_CNT: {
				fbin.read(reinterpret_cast<char*>(&word32b), sizeof(word32b));
				if (debug) cout << "GET_ADC_WORD_CNT: " << "0x" << uppercase << hex << word32b << endl;
				if (((word32b >> 28) == 0xF) && (((word32b >> 12) & 0xF) == 0xF)) {
					unsigned int adcCntTrue = ((word32b & 0xFFF) << 12) | ((word32b >> 16) & 0xFFF);
					fems[currFEMSlot]->setADCCntTrue(adcCntTrue);
					state = STATE::GET_EVENT_NUM;
				}
				else {
					fems[currFEMSlot]->setFEMSlot(0xFFFF);
					state = STATE::WAIT_FEM_HEADER_R;
				}
				break;
			}
		  case STATE::GET_EVENT_NUM: {
				fbin.read(reinterpret_cast<char*>(&word32b), sizeof(word32b));
				if (debug) cout << "GET_EVENT_NUM: " << "0x" << uppercase << hex << word32b << endl;
				if (((word32b >> 28) == 0xF) && (((word32b >> 12) & 0xF) == 0xF)) {
					unsigned int eventNum = ((word32b & 0xFFF) << 12) | ((word32b >> 16) & 0xFFF);
					fems[currFEMSlot]->setEventNum(eventNum);
					state = STATE::GET_FRAME_NUM;
				}
				else {
					fems[currFEMSlot]->setFEMSlot(0xFFFF);
					state = STATE::WAIT_FEM_HEADER_R;
				}
				break;
			}
		  case STATE::GET_FRAME_NUM: {
				fbin.read(reinterpret_cast<char*>(&word32b), sizeof(word32b));
				if (debug) cout << "GET_FRAME_NUM: " << "0x" << uppercase << hex << word32b << endl;
				if (((word32b >> 28) == 0xF) && (((word32b >> 12) & 0xF) == 0xF)) {
					unsigned int frameNum = ((word32b & 0xFFF) << 12) | ((word32b >> 16) & 0xFFF);
					fems[currFEMSlot]->setFrameNum(frameNum);
					state = STATE::GET_ADC_WORD_CHECKSUM;
				}
				else {
					fems[currFEMSlot]->setFEMSlot(0xFFFF);
					state = STATE::WAIT_FEM_HEADER_R;
				}
				break;
			}
		  case STATE::GET_ADC_WORD_CHECKSUM: {
				fbin.read(reinterpret_cast<char*>(&word32b), sizeof(word32b));
				if (debug) cout << "GET_ADC_WORD_CHECKSUM: " << "0x" << uppercase << hex << word32b << endl;
				if (((word32b >> 28) == 0xF) && (((word32b >> 12) & 0xF) == 0xF)) {
					unsigned int adcChecksumTrue = ((word32b & 0xFFF) << 12) | ((word32b >> 16) & 0xFFF);
					fems[currFEMSlot]->setADCChecksumTrue(adcChecksumTrue);
					state = STATE::GET_SAMPLE_NUM;
				}
				else {
					fems[currFEMSlot]->setFEMSlot(0xFFFF);
					state = STATE::WAIT_FEM_HEADER_R;
				}
				break;
			}
		  case STATE::GET_SAMPLE_NUM: {
				fbin.read(reinterpret_cast<char*>(&word32b), sizeof(word32b));
				if (debug) cout << "GET_SAMPLE_NUM: " << "0x" << uppercase << hex << word32b << endl;
				if (((word32b >> 28) == 0xF) && (((word32b >> 12) & 0xF) == 0xF)) {
					state = STATE::WAIT_CHANNEL_START;
				}
				else {
					fems[currFEMSlot]->setFEMSlot(0xFFFF);
					state = STATE::WAIT_FEM_HEADER_R;
				}
				break;
			}
		  case STATE::WAIT_CHANNEL_START: {
				fbin.read(reinterpret_cast<char*>(&word16b), sizeof(word16b));
				if (debug) cout << "WAIT_CHANNEL_START: " << "0x" << uppercase << hex << word16b << endl;
				if (word16b == 0x0) {
					fems[currFEMSlot]->setADCCntReco(currADCWordCnt);
					fems[currFEMSlot]->setADCChecksumReco(currADCChecksum);
					state = STATE::GET_EVENT_END;
				}
				else if (word16b == FEM_HEADER) state = STATE::GET_FEM_HEADER_L;
				else if ((word16b >> 12) == 0x1) {
					++currADCWordCnt;
					currADCChecksum += word16b;
					unsigned short channelNum = (word16b & 0x3F);
					unsigned short frameNum = ((word16b >> 6) & 0x3F);
					channel->setChannelNum(channelNum);
					channel->setFrameNum(frameNum);
					channel->clearROITimestamps();
					channel->clearROIIDs();
					channel->clearROIADCs();
					channel->clearROISampleNums();
					currROIID = 0;
					roiStartMissCntInc = true;
					currROIStartMissCnt = 0;
					currROIEndMissCnt = 0;
					state = STATE::WAIT_ROI_START;
				}
				else {
					++currADCWordCnt;
					currADCChecksum += word16b;
					state = STATE::WAIT_CHANNEL_START;
				}
				break;
			}
		  case STATE::WAIT_ROI_START: {
				fbin.read(reinterpret_cast<char*>(&word16b), sizeof(word16b));
				if (debug) cout << "WAIT_ROI_START: " << "0x" << uppercase << hex << word16b << endl;
				if (word16b == 0x0) {
					channel->setROIStartMissCnt(currROIStartMissCnt);
					channel->setROIEndMissCnt(currROIEndMissCnt);
					fems[currFEMSlot]->pushChannel(*channel);
					fems[currFEMSlot]->setADCCntReco(currADCWordCnt);
					fems[currFEMSlot]->setADCChecksumReco(currADCChecksum);
					state = STATE::GET_EVENT_END;
				}
				else if (word16b == FEM_HEADER) {
					channel->setROIStartMissCnt(currROIStartMissCnt);
					channel->setROIEndMissCnt(currROIEndMissCnt);
					fems[currFEMSlot]->pushChannel(*channel);
					state = STATE::GET_FEM_HEADER_L;
				}
				else if ((word16b >> 12) == 0x1) {
					++currADCWordCnt;
					currADCChecksum += word16b;
					channel->setROIStartMissCnt(currROIStartMissCnt);
					channel->setROIEndMissCnt(currROIEndMissCnt);
					fems[currFEMSlot]->pushChannel(*channel);
					channel->clearROITimestamps();
					channel->clearROIIDs();
					channel->clearROIADCs();
					channel->clearROISampleNums();
					currROIID = 0;
					roiStartMissCntInc = true;
					currROIStartMissCnt = 0;
					currROIEndMissCnt = 0;
					unsigned short channelNum = (word16b & 0x3F);
					unsigned short frameNum = ((word16b >> 6) & 0x3F);
					channel->setChannelNum(channelNum);
					channel->setFrameNum(frameNum);
					state = STATE::WAIT_ROI_START;
				}
				else if ((word16b >> 14) == 0b01) {
					++currADCWordCnt;
					currADCChecksum += word16b;
					unsigned short roiTimestamp = (word16b & 0x3FFF);
					channel->pushROITimestamp(roiTimestamp);
					++currROIID;
					currROISampleNumCnt = 0;
					roiStartMissCntInc = true;
					state = STATE::WAIT_ROI_END;
				}
				else {
					if (roiStartMissCntInc) {
						++currROIStartMissCnt;
						roiStartMissCntInc = false;
					}
					++currADCWordCnt;
					currADCChecksum += word16b;
					state = STATE::WAIT_ROI_START;
				}
				break;
			}
		  case STATE::WAIT_ROI_END: {
				fbin.read(reinterpret_cast<char*>(&word16b), sizeof(word16b));			
				if (debug) cout << "WAIT_ROI_END: " << "0x" << uppercase << hex << word16b << endl;
				if (word16b == 0x0) {
					++currROIEndMissCnt;
					channel->setROIStartMissCnt(currROIStartMissCnt);
					channel->setROIEndMissCnt(currROIEndMissCnt);
					fems[currFEMSlot]->pushChannel(*channel);
					fems[currFEMSlot]->setADCCntReco(currADCWordCnt);
					fems[currFEMSlot]->setADCChecksumReco(currADCChecksum);
					state = STATE::GET_EVENT_END;
				}
				else if (word16b == FEM_HEADER) {
					++currROIEndMissCnt;
					channel->setROIStartMissCnt(currROIStartMissCnt);
					channel->setROIEndMissCnt(currROIEndMissCnt);
					fems[currFEMSlot]->pushChannel(*channel);
					state = STATE::GET_FEM_HEADER_L;
				}
				else if ((word16b >> 12) == 0x1) {
					++currROIEndMissCnt;
					++currADCWordCnt;
					currADCChecksum += word16b;
					channel->setROIStartMissCnt(currROIStartMissCnt);
					channel->setROIEndMissCnt(currROIEndMissCnt);
					fems[currFEMSlot]->pushChannel(*channel);
					channel->clearROITimestamps();
					channel->clearROIIDs();
					channel->clearROIADCs();
					channel->clearROISampleNums();
					currROIID = 0;
					roiStartMissCntInc = true;
					currROIStartMissCnt = 0;
					currROIEndMissCnt = 0;
					unsigned short channelNum = (word16b & 0x3F);
					unsigned short frameNum = ((word16b >> 6) & 0x3F);
					channel->setChannelNum(channelNum);
					channel->setFrameNum(frameNum);
					state = STATE::WAIT_ROI_START;
				}
				else if ((word16b >> 14) == 0b01) {
					++currROIEndMissCnt;
					++currADCWordCnt;
					currADCChecksum += word16b;
					unsigned short roiTimestamp = (word16b & 0x3FFF);
					channel->pushROITimestamp(roiTimestamp);
					++currROIID;
					currROISampleNumCnt = 0;
					roiStartMissCntInc = true;
					state = STATE::WAIT_ROI_END;
				}
				else if ((word16b >> 12) == 0x3) {
					++currADCWordCnt;
					currADCChecksum += word16b;
					unsigned short adcLastSample = (word16b & 0xFFF);
					channel->pushROIID(currROIID-1);
					channel->pushROIADC(adcLastSample);
					channel->pushROISampleNum((channel->getROITimestamps()[currROIID-1] + currROISampleNumCnt));
					state = STATE::WAIT_ROI_START;
				}
				else {
					++currADCWordCnt;
					currADCChecksum += word16b;
					if ((word16b >> 12) == 0x2) {
						currROIADC = (word16b & 0xFFF);
						channel->pushROIID(currROIID-1);
						channel->pushROIADC(currROIADC);
						channel->pushROISampleNum((channel->getROITimestamps()[currROIID-1] + currROISampleNumCnt));
						++currROISampleNumCnt;
					}
					else if ((word16b >> 15) == 0b1) {
						bitset<15> huffmanBits((word16b & 0x7FFF));
						stack<short> huffmanCodes;
						unsigned short nzero = 0;
						for (int bit=14; bit>-1; --bit) {
							if (huffmanBits[bit]) {
								huffmanCodes.push(nzero);
								nzero = 0;
							}
							else ++nzero;
						}
						while (!huffmanCodes.empty()) {
								currROIADC += HUFFMAN_TABLE.at(huffmanCodes.top());
								channel->pushROIID(currROIID-1);
								channel->pushROIADC(currROIADC);
								channel->pushROISampleNum((channel->getROITimestamps()[currROIID-1] + currROISampleNumCnt));
								++currROISampleNumCnt;
								huffmanCodes.pop();
						}
					}
					state = STATE::WAIT_ROI_END;
				}
				break;
			}
			case STATE::GET_FEM_HEADER_L: {
				fbin.read(reinterpret_cast<char*>(&word16b), sizeof(word16b));
				if (debug) cout << "GET_FEM_HEADER_L: " << "0x" << uppercase << hex << word16b << endl;
				if ((currFEMSlot > 2) && (currFEMSlot < 19)) {
					fems[currFEMSlot]->setADCCntReco(currADCWordCnt);
					fems[currFEMSlot]->setADCChecksumReco(currADCChecksum);
				}
				currROISampleNumCnt = 0;
				if (word16b == 0xFFFF) {
					event->Fill();
					++eventID;
					eventEndMiss = true;
					allFEMHeaderMiss = true;
					for (auto& fem : fems) fem.second->setFEMSlot(0xFFFF);
					state = STATE::WAIT_FEM_HEADER;
				}
				else if ((word16b >> 12) == 0xF) {
					currFEMSlot = word16b & 0x1F;
					if ((currFEMSlot > 2) && (currFEMSlot < 19)) {
						unsigned short femID = (word16b >> 5) & 0xF;
						bool test = static_cast<bool>(((word16b >> 9) & 0x1));
						bool overflow = static_cast<bool>(((word16b >> 10) & 0x1));
						bool full = static_cast<bool>(((word16b >> 11) & 0x1));
						if (fems.find(currFEMSlot) == fems.end()) {
							fems[currFEMSlot] = new femSN();
							event->Branch(Form("fem%d",currFEMSlot), "femSN", &fems[currFEMSlot]);
						}
						fems[currFEMSlot] = fems[currFEMSlot];
						fems[currFEMSlot]->setFEMSlot(currFEMSlot);
						fems[currFEMSlot]->setFEMID(femID);
						fems[currFEMSlot]->setTest(test);
						fems[currFEMSlot]->setOverflow(overflow);
						fems[currFEMSlot]->setFull(full);
						fems[currFEMSlot]->clearChannels();
						currADCWordCnt = 0;
						currADCChecksum = 0;
						state = STATE::GET_ADC_WORD_CNT;
					}
					else state = STATE::WAIT_FEM_HEADER_R;
				}
				else state = STATE::WAIT_FEM_HEADER_R;
				break;
			}
			case STATE::WAIT_FEM_HEADER_R: {
				fbin.read(reinterpret_cast<char*>(&word16b), sizeof(word16b));
				if (debug) cout << "WAIT_FEM_HEADER_R: " << "0x" << uppercase << hex << word16b << endl;
				if (word16b == 0x0) state = STATE::GET_EVENT_END;
				else if (word16b == 0xFFFF) state = STATE::GET_FEM_HEADER_L;
				else state = STATE::WAIT_FEM_HEADER_R;
				break;
			}
			case STATE::GET_EVENT_END: {
				fbin.read(reinterpret_cast<char*>(&word16b), sizeof(word16b));
				if (debug) cout << "GET_EVENT_END: " << "0x" << uppercase << hex << word16b << endl;
				currROISampleNumCnt = 0;
				if (word16b == EVENT_END) {
					eventEndMiss = false;	
					state = STATE::WAIT_EVENT_START;
				}
				else if (word16b == FEM_HEADER) {
					eventEndMiss = true;
					state = STATE::GET_FEM_HEADER_L;
				}
				else state = STATE::GET_EVENT_END;
				break;
			}
		}

		if (progressBar) {
			streamsize count = fbin.gcount();
			bytesRead += count;
			double progress = static_cast<double>(bytesRead) / totalSize;
			displayProgressBar(progress);
		}
	}
	event->Fill();
	if (progressBar) cout << endl;

	froot->Write("", TObject::kOverwrite);
	froot->Close();
	flog.close();
	fbin.close();

	return 0;
}
