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
#include <numeric>
#include <filesystem>
#include <cmath>

using namespace std;

int main(int argc, char* argv[]) {
  bool print=false; // change if you want to print detailed decoder output
  int femHdrCount=0;
  uint32_t fem, fem_idx;
  bool countheader=false;
  bool lookupFEM=false;
  int32_t  wordcount_lower12bit, wordcount_higher12bit, header_wordcount = -1, wordcount = -1;
  int64_t frame = -1, frame_lower12bit, frame_higher12bit;
  uint16_t sample, sample_lower8bits, sample_higher4bits;
  bool inFrame = false;
  int endofFrame = 0;
  constexpr int nfems = 16;
  std::map<int,int> wordcount_diff_count = {};
  std::array<int, nfems> missed_femheaders = {};
  std::array<int, nfems> previous_frame = {};
  previous_frame.fill(-1);
  std::map<int,int> frame_diff_count = {};
  int channel, previous_channel = -1;
  std::array<int, nfems> missed_channelstart = {};
  int inADCdata = false;
  int firstframe;
  bool foundfirstframe = false;

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

  std::string hist_filename = "run" + std::string(argv[2]) + "_tpc" + std::string(argv[3]) + "_hists.txt";

  if (std::filesystem::exists(hist_filename)) {
        std::ifstream infile(hist_filename);
        std::string line;
        std::getline(infile, line);

        while (std::getline(infile, line)) {
            if (line.empty()) break;
            std::istringstream iss(line);
            int diff, count;
            if (iss >> diff >> count) {
              frame_diff_count[diff] = count;
            }
        }

        while (std::getline(infile, line)) {
          if (line.empty()) break;
          std::istringstream iss(line);
          int diff, count;
          if (iss >> diff >> count) {
            wordcount_diff_count[diff] = count;
          }
        }
      }

  while( binFile.peek() != EOF ){
    uint32_t word32b;
    binFile.read( reinterpret_cast<char*>(&word32b), sizeof(word32b) );

    std::cout.setf ( std::ios::hex, std::ios::basefield );  // set hex as the basefield
    std::cout.setf ( std::ios::showbase ); // activate showbase    i.e with prefix 0x

    //std::cout << "word: " << std::hex << word32b << std::endl;

    uint16_t first16b = word32b & 0xffff; //right 16 bit word
    uint16_t last16b = (word32b>>16) & 0xffff; // left 16 bit word
    if(word32b == 0xffffffff) {
      femHdrCount=1;
      lookupFEM=true;
      if ((inFrame == true) && (frame>1)){
        if (print){
          std::cout << "Missing end of frame marker for frame " << std::dec << frame << std::endl;
        }
        endofFrame++;
      }
      inFrame=true;
    }
    else if (word32b  == 0xe0000000){
      countheader=false;
      inFrame=false;
    }

    else if (inFrame){
      if(lookupFEM==true){
        if ((last16b >>8 == 0xf1) && (first16b == 0xffff)){ // there is no word which identifies end of header words for first FEM and start of next FEM , so we have to use this way to identify FEM words instead of using femHdrCount==2
          countheader=true;
          if ((previous_channel != -1) && (frame>1)){
            int missing_channels = 63 - previous_channel;
            if (missing_channels > 0) {
                if (print){
                  std::cout << "Missing last " << std::dec << missing_channels << " channels at end of fem data for frame " << frame << " and fem " << fem << std::endl;
                }
                missed_channelstart[fem_idx] += missing_channels;
            }
          }

          previous_channel = -1;
          channel = 0;

          if (frame>1){
            int wordcount_diff = header_wordcount - wordcount;
            wordcount_diff_count[wordcount_diff]++;
            if (wordcount_diff < 0){
              if (print){
                std::cout << "For frame " << std::dec << frame << ", fem " << fem << " header wordcount: " << header_wordcount << " does not match manual wordcount: " << wordcount << std::endl;
              }  
            }
          }

          fem =(last16b&0x1f);
          fem_idx = fem-3;
          femHdrCount=1;
          lookupFEM=false;
        }
      }

      if(countheader==true){
        if (femHdrCount > 0) { // check that each expected word in header after header start starts with F
          if ( !(((last16b & 0xF000) == 0xF000 ) && ( (first16b & 0xF000) == 0xF000 )) ) {
            if (print){
              std::cout << "FEM header word " << femHdrCount - 1 << " for frame " << std::dec << frame << " and fem " << fem << " is missing." << std::endl;
            }
              missed_femheaders[fem_idx]++;
          }
        }

        femHdrCount+=1;

        if (femHdrCount==3){ // ADC word count
            wordcount_lower12bit= (last16b & 0xfff);
            wordcount_higher12bit= (first16b & 0xfff);

            header_wordcount = wordcount_higher12bit<<12|wordcount_lower12bit;
            wordcount = 0;
        }

        
        if(femHdrCount==5){
            frame_lower12bit= (last16b & 0xfff);
            frame_higher12bit= (first16b & 0xfff);
            frame = frame_higher12bit<<12|frame_lower12bit;

            if ((frame > 1) && (!foundfirstframe)){
              firstframe = frame;
              foundfirstframe = true;
            }

            if ((previous_frame[fem_idx] > 1) && (frame > 1)){
              int frame_diff = frame - previous_frame[fem_idx];
              frame_diff_count[frame_diff]++;
              if ((frame_diff != 1) && (frame_diff != 4)){
                if (print){
                  std::cout << "Difference between current frame and previous frame is " << std::dec << frame_diff << " frames for frame " << frame << " and previous frame " << previous_frame[fem_idx] << " for fem " << fem << std::endl;  
                }
              }
            }
            previous_frame[fem_idx] = frame;

        }


        else if(femHdrCount==7){

            femHdrCount=-1;
            countheader=false;
            lookupFEM=true;
        }
    }

    else{

      if(first16b>>12 == 0x1){ // check for start of channel
        channel = (first16b & 0x3f);
        wordcount += 1;
        int channel_diff = channel - previous_channel;
        if ((channel_diff > 1) && (frame>1)){
          if (print){
            std::cout << "Channel starts from " << std::dec << previous_channel+1 << " and " << channel-1 << " are missing for frame " << frame << " for fem " << fem << std::endl;  
          }
            missed_channelstart[fem_idx] += channel_diff-1;
        }
        if (channel_diff < 0){
          if (print){
            std::cout << "CHANNELS ARE BEING REPEATED, FEM DATA IS CORRUPT" << std::endl;
          }          
        }
        previous_channel = channel;
      }
        
      else{
          wordcount += 1;
      }

      if(last16b>>12 == 0x1){ // check for start of channel
        channel = (last16b & 0x3f);
        wordcount += 1;
        int channel_diff = channel - previous_channel;
        if ((channel_diff > 1) && (frame>1)){
          if (print){
            std::cout << "Channel starts from " << std::dec << previous_channel+1 << " and " << channel-1 << " are missing for frame " << frame << " for fem " << fem << std::endl;  
          }
          missed_channelstart[fem_idx] += channel_diff-1;
        }

        if (channel_diff < 0){
          if (print){
            std::cout << "CHANNELS ARE BEING REPEATED, FEM DATA IS CORRUPT" << std::endl;
          }          
        }

        previous_channel = channel;
      }
        
      else{
          wordcount += 1;
      }


    }

    }//end of else
  else{ // for words at the beginning of a file before a start of frame word

  }
  }//end of while loop

  int nframes = frame - firstframe;

  bool rollover = (nframes < -1);
  if (rollover){
    nframes += 16777216;
  }
  double missed_frameend_perframe = endofFrame / nframes;

  std::array<double, nfems> missed_femheaders_perframe;
  std::array<double, nfems> missed_channelstarts_perframe;
  
  for (int fem = 0; fem < nfems; ++fem) {
    missed_femheaders_perframe[fem] = static_cast<double>(missed_femheaders[fem]) / nframes;
    missed_channelstarts_perframe[fem] = static_cast<double>(missed_channelstart[fem]) / nframes;
  }
  
  std::string outfilename = "run" + std::string(argv[2]) + "_tpc" + std::string(argv[3]) + "_dataformat_metrics.txt";
  bool new_file = !std::filesystem::exists(outfilename) || std::filesystem::file_size(outfilename) == 0;
  std::ofstream outfile(outfilename, std::ios::app);
  if (new_file) {
    outfile << "FirstFrame\tLastFrame\tMissedFrameEndRate\tFEMAvg-MissedFEMHeaderRate\tFEMStdev-MissedFEMHeaderRate\tFEMAvg-MissedChannelStartRate\tFEMStdev-MissedChannelStartRate\n";
  }

  auto mean = [](const auto &arr) {
  return std::accumulate(arr.begin(), arr.end(), 0.0) / arr.size();
  };

  auto stdev = [](const auto &arr) {
  double m = std::accumulate(arr.begin(), arr.end(), 0.0) / arr.size();
  double sq_sum = std::inner_product(arr.begin(), arr.end(), arr.begin(), 0.0);
  return std::sqrt(sq_sum / arr.size() - m * m);
  };

  double avg_missed_femheaders_perframe = mean(missed_femheaders_perframe);
  double avg_missed_channelstart_perframe = mean(missed_channelstarts_perframe);

  double std_missed_femheaders_perframe = stdev(missed_femheaders_perframe);
  double std_missed_channelstart_perframe = stdev(missed_channelstarts_perframe);

  outfile << firstframe << "\t" << frame << "\t" << missed_frameend_perframe << "\t" << avg_missed_femheaders_perframe << "\t" << std_missed_femheaders_perframe << "\t" << avg_missed_channelstart_perframe << "\t" << std_missed_channelstart_perframe << "\n";

  std::ofstream outfile2(hist_filename);
  outfile2 << "FrameDiff\tCount\n";
  for (const auto &[d,c] : frame_diff_count)
    outfile2 << d << "\t" << c << "\n";
  
    outfile2 << "\n";

  outfile2 << "WordCountDiff\tCount\n";
  for (const auto &[d, c] : wordcount_diff_count) {
      outfile2 << d << "\t" << c << "\n";
  }
  }// end of int main function
