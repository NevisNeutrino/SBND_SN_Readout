#include <iostream>
#include <fstream>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <map>
#include <tuple>
#include <vector>
#include <typeinfo>
#include <ctime>
#include <sys/time.h>
#include <cstdint>
#include <bitset>
#include <algorithm>
#include <numeric>
#include <filesystem>

using namespace std;

int main(int argc, char* argv[]) {
  bool print=false; // change if you want to print detailed decoder output
  int femHdrCount=0;
  int32_t fem, fem_idx;
  bool countheader=false;
  bool lookupFEM=false;
  bool inFrame = false;
  int64_t frame_lower12bit, frame_higher12bit, frame=-1;
  constexpr int nfems = 16;
  constexpr int nchannels = 64;
  bool inADCdata = false, firstval = false;
  std::vector<int> adc_vals;
  int roistart = -1, roiend = -1, baseline = -1, amplitude = -1, adcval = -1;
  std::vector<std::vector<int>> roistart_count(nfems, std::vector<int>(nchannels, 0));
  std::vector<std::vector<double>> roistart_sum(nfems, std::vector<double>(nchannels, 0.0));
  std::vector<std::vector<int>> roiend_count(nfems, std::vector<int>(nchannels, 0));
  std::vector<std::vector<double>> roiend_sum(nfems, std::vector<double>(nchannels, 0.0));
  std::vector<std::vector<int>> baseline_count(nfems, std::vector<int>(nchannels, 0));
  std::vector<std::vector<double>> baseline_sum(nfems, std::vector<double>(nchannels, 0.0));
  std::vector<std::vector<int>> amplitude_count(nfems, std::vector<int>(nchannels, 0));
  std::vector<std::vector<double>> amplitude_sum(nfems, std::vector<double>(nchannels, 0.0));
  std::vector<std::vector<int>> missed_ROIstart(nfems, std::vector<int>(nchannels, 0));
  std::vector<std::vector<int>> missed_ROIend(nfems, std::vector<int>(nchannels, 0));
  int channel = -1;
  std::vector<int> adcdiff;
  int firstframe;
  bool foundfirstframe = false;

  std::vector<std::pair<std::string, int>> huffmanTable = {
    {"1", 0},
    {"01", -1},
    {"001", 1},
    {"0001", -2},
    {"00001", 2},
    {"000001", -3},
    {"0000001", 3}
  };

  if (argc < 4) {
    std::cerr << "Usage: " << argv[0] << " inputfile run_number tpc_number" << std::endl;
    return 1;
  }

  const char* filename = argv[1];
  std::ifstream binFile(filename, std::ios::binary);
  if (!binFile) {
    std::cerr << "Error: could not open file " << filename << std::endl;
    return 1;
  }

  while( binFile.peek() != EOF ){
    uint32_t word32b;
    binFile.read( reinterpret_cast<char*>(&word32b), sizeof(word32b) );

    std::cout.setf ( std::ios::hex, std::ios::basefield );  // set hex as the basefield
    std::cout.setf ( std::ios::showbase ); // activate showbase    i.e with prefix 0x

    uint16_t first16b = word32b & 0xffff; //right 16 bit word
    uint16_t last16b = (word32b>>16) & 0xffff; // left 16 bit word

    if(word32b == 0xffffffff) {
      femHdrCount=1;
      lookupFEM=true;
      inFrame=true;
    }
    else if (word32b  == 0xe0000000){
      countheader=false;
      inFrame=false;
    }

    else{
      if(lookupFEM==true){
        if ((last16b >>8 == 0xf1) and (first16b == 0xffff)){ // there is no word which identifies end of header words for first FEM and start of next FEM , so we have to use this way to identify FEM words instead of using femHdrCount==2
          if ((frame > 1) && (channel > -1)){
             int& scount = roistart_count[fem_idx][channel];
             double& ssum = roistart_sum[fem_idx][channel];
             ssum += roistart;
             scount += 1;

             int& ecount = roiend_count[fem_idx][channel];
             double& esum = roiend_sum[fem_idx][channel];
             esum += roiend;
             ecount += 1;

           }

          if ((inADCdata == true) && (frame>1) && (channel > -1)){
            if (print){
              std::cout << "Missing ROI end for channel " << std::dec << channel << " for frame " << frame << " and fem " << fem << std::endl;
            }
            missed_ROIend[fem_idx][channel]++;
          }

          roistart = 0;
          roiend = 0;
          channel = -1; 
          inADCdata == false;

          fem =(last16b&0x1f);
          fem_idx = fem-3;
          countheader=true;
          femHdrCount=1;
          lookupFEM=false;
        }
      }

      if(countheader==true){
        femHdrCount+=1;
        
        if(femHdrCount==5){
            frame_lower12bit= (last16b & 0xfff);
            frame_higher12bit= (first16b & 0xfff);
            frame = frame_higher12bit<<12|frame_lower12bit;

            if ((frame > 1) && (!foundfirstframe)){
              firstframe = frame;
              foundfirstframe = true;
            }
        
        }

        else if(femHdrCount==7){

            femHdrCount=-1;
            countheader=false;
            lookupFEM=true;
        }
    }

    else{
        
        if(first16b>>12 == 0x1){
            if ((inADCdata == true) && (frame>1) && (channel > -1)){
              if (print){
               std::cout << "Missing ROI end for channel " << std::dec << channel << " for frame " << frame << " and fem " << fem << std::endl;
              }
              missed_ROIend[fem_idx][channel]++;
           }

            inADCdata = false;
            if ((channel > -1) && (frame>1)){
                int& scount = roistart_count[fem_idx][channel];
                double& ssum = roistart_sum[fem_idx][channel];
                ssum += roistart;
                scount += 1;

                int& ecount = roiend_count[fem_idx][channel];
                double& esum = roiend_sum[fem_idx][channel];
                esum += roiend;
                ecount += 1;

            }
            channel = (first16b & 0x3f);   
            roistart = 0;
            roiend = 0;
        }
        
        else if ((first16b & 0xC000) == 0x4000){
          if ((inADCdata == true) && (frame>1) && (channel > -1)){
            if (print){
              std::cout << "Missing ROI end for channel " << std::dec << channel << " for frame " << frame << " and fem " << fem << std::endl;
            }
            missed_ROIend[fem_idx][channel]++;
          }
          inADCdata = true;

          firstval = true;
          roistart++;
        }

        else if (inADCdata) {
            if (first16b>>12 == 0x2){
                adcval = (first16b & 0xfff);
                if ((firstval == true) && (frame>1) && (channel > -1)){
                  baseline = adcval;
                  int& count = baseline_count[fem_idx][channel];
                  double& sum = baseline_sum[fem_idx][channel];
                  sum += baseline;
                  count += 1;
                  firstval = false;
                }
                adc_vals.push_back(adcval);
            }

            else if (first16b>>12 == 0x3){
                adcval = (first16b & 0xfff);
                inADCdata = false;
                adc_vals.push_back(adcval);
                if ((frame>1) && (channel > -1)){
                  amplitude = *std::max_element(adc_vals.begin(), adc_vals.end());
                  int& count = amplitude_count[fem_idx][channel];
                  double& sum = amplitude_sum[fem_idx][channel];
                  sum += amplitude;
                  count += 1;
                }  
                adc_vals.clear();
                roiend++;
            }

	        else if ((first16b & 0x8000) == 0x8000) { 
                std::bitset<16> bits(first16b);
                bool foundFirstOne = false;
                int zeroCount = 0;
                for (int i = 0; i < 16; ++i) { // Start from LSB (bit 0)       
                    if (!foundFirstOne) {
                        if (bits[i] == 1) {
                            foundFirstOne = true;
                        }
                    } else {
                        if (bits[i] == 0) {
                            zeroCount++;
                        } else { // Found next 1 
                    
                            switch (zeroCount) {
                                case 0: adcdiff.emplace_back(0); break;  // 1                     
                                                                              
                                case 1: adcdiff.emplace_back(-1); break; // 01                    
                                                                              
                                case 2: adcdiff.emplace_back(+1); break; // 001                   
                                                                              
			                          case 3: adcdiff.emplace_back(-2); break; // 0001                  
                                                                              
                                case 4: adcdiff.emplace_back(+2); break; // 00001                 
                                                                              
                                case 5: adcdiff.emplace_back(-3); break; // 000001                
                                                                              
                                case 6: adcdiff.emplace_back(+3); break; // 0000001               
                                                                              
                                default: break; // Ignore if zeroCount exceeds the pattern        
                                                                              
                            }

                        zeroCount = 0;

                        }
                    }
                }
	            for (int d : adcdiff){
                    adcval += d;
                    adc_vals.push_back(adcval);
                }
                adcdiff.clear();
            }
          }

        else if(first16b>>12 == 0x3){
          if ((frame>1) && (channel > -1)){
            if (print){
              std::cout << "Missing ROI start for channel " << std::dec << channel << " for frame " << frame << " and fem " << fem << std::endl;
            }
            missed_ROIstart[fem_idx][channel]++;
            roiend++;
          }
          inADCdata = false;   
        }
        
        if(last16b>>12 == 0x1){
            if ((inADCdata == true) && (frame>1) && (channel > -1)){
              if (print){
               std::cout << "Missing ROI end for channel " << std::dec << channel << " for frame " << frame << " and fem " << fem << std::endl;
              }
              missed_ROIend[fem_idx][channel]++;
            }

            inADCdata = false;
            if ((channel > -1) && (frame>1)){
                int& scount = roistart_count[fem_idx][channel];
                double& ssum = roistart_sum[fem_idx][channel];
                ssum += roistart;
                scount += 1;

                int& ecount = roiend_count[fem_idx][channel];
                double& esum = roiend_sum[fem_idx][channel];
                esum += roiend;
                ecount += 1;

            }
            channel = (last16b & 0x3f);
            roistart = 0;
            roiend = 0;
        }
        
        else if ((last16b & 0xC000) == 0x4000){
          if ((inADCdata == true) && (frame>1) && (channel > -1)){
            if (print){
              std::cout << "Missing ROI end for channel " << std::dec << channel << " for frame " << frame << " and fem " << fem << std::endl;
            }
            missed_ROIend[fem_idx][channel]++;
          }
          inADCdata = true;
          firstval = true;
          roistart++;
        }
        
        else if (inADCdata) {
            if (last16b>>12 == 0x2){
                adcval = (last16b & 0xfff);
                if ((firstval == true) && (frame>1) && (channel > -1)){
                  baseline = adcval;
                  int& count = baseline_count[fem_idx][channel];
                  double& sum = baseline_sum[fem_idx][channel];
                  sum += baseline;
                  count += 1;
                  firstval = false;
               }   
               adc_vals.push_back(adcval);      
            }

            else if (last16b>>12 == 0x3){
                adcval = (last16b & 0xfff);
                inADCdata = false;
                adc_vals.push_back(adcval);
                if ((frame>1) && (channel > -1)){
                  amplitude = *std::max_element(adc_vals.begin(), adc_vals.end());
                  int& count = amplitude_count[fem_idx][channel];
                  double& sum = amplitude_sum[fem_idx][channel];
                  sum += amplitude;
                  count += 1;
                }  
                adc_vals.clear();
                roiend++;
            }
	
	        else if ((last16b & 0x8000) == 0x8000) {               
                std::bitset<16> bits(last16b);
                bool foundFirstOne = false;
                int zeroCount = 0;
                for (int i = 0; i < 16; ++i) { // Start from LSB (bit 0)       
                if (!foundFirstOne) {
                    if (bits[i] == 1) {
                    foundFirstOne = true;
                    }
                    } else {
                    if (bits[i] == 0) {
                        zeroCount++;
                    } else { // Found next 1 
                    
                        switch (zeroCount) {
                            case 0: adcdiff.emplace_back(0); break;  // 1                     
                                                                              
                            case 1: adcdiff.emplace_back(-1); break; // 01                    
                                                                              
                            case 2: adcdiff.emplace_back(+1); break; // 001                   
                                                                              
			                      case 3: adcdiff.emplace_back(-2); break; // 0001                  
                                                                              
                            case 4: adcdiff.emplace_back(+2); break; // 00001                 
                                                                              
                            case 5: adcdiff.emplace_back(-3); break; // 000001                
                                                                              
                            case 6: adcdiff.emplace_back(+3); break; // 0000001               
                                                                              
                            default: break; // Ignore if zeroCount exceeds the pattern        
                                                                              
                        }

                        zeroCount = 0;

                    }
                }
                }
	            for (int d : adcdiff){
                    adcval += d;
                    adc_vals.push_back(adcval);
                }
                adcdiff.clear();
                }
      }
      
      else if(first16b>>12 == 0x3){
          if ((frame>1) && (channel > -1)){
            if (print){
              std::cout << "Missing ROI start for channel " << std::dec << channel << " for frame " << frame << " and fem " << fem << std::endl;
            }
            missed_ROIstart[fem_idx][channel]++;
            roiend++;
          }
        inADCdata = false;   
      }

     }
    }//end of else

  }//end of while loop  

  std::ofstream outfile("run" + std::string(argv[2]) + "_tpc" + std::string(argv[3]) + "_channel_metrics.txt");
  outfile << "Frame " << firstframe << "-" << frame << "\n";
  outfile << "FEM\tChannel\tNROIStartRate\tNROIEndRate\tAvgBaseline\tAvgAmplitude\tRatioMissedROIstartperROIstart\tRatioMissedROIendperROIend\n";
  
  for (int fem = 0; fem < nfems; ++fem) {
    for (int ch = 0; ch < nchannels; ++ch) {
      double roistart = (roistart_count[fem][ch] > 0) ? roistart_sum[fem][ch] / roistart_count[fem][ch]: 0.0;
      double roiend = (roiend_count[fem][ch] > 0) ? roiend_sum[fem][ch] / roiend_count[fem][ch]: 0.0;  
      double baseline = (baseline_count[fem][ch] > 0) ? baseline_sum[fem][ch] / baseline_count[fem][ch]: 0.0;  
      double amplitude = (amplitude_count[fem][ch] > 0) ? amplitude_sum[fem][ch] / amplitude_count[fem][ch]: 0.0;  

      double missed_start_per_roi = (roistart_sum[fem][ch]) ? missed_ROIstart[fem][ch] / (roistart_sum[fem][ch]): 0.0;
      double missed_end_per_roi = (roiend_sum[fem][ch]) ? missed_ROIend[fem][ch] / (roiend_sum[fem][ch]): 0.0;

      outfile << fem+3 << "\t" << ch << "\t" << roistart << "\t" << roiend << "\t" << baseline << "\t" << amplitude << "\t" << missed_start_per_roi << "\t" << missed_end_per_roi << "\n";
    
    }
  }


}// end of int main function
