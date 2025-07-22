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

using namespace std;

int main(int argc, char* argv[]) {
  int femHdrCount=0;
  uint32_t fem;
  bool countheader=false;
  bool lookupFEM=false;
  int64_t event_lower12bit, event_higher12bit, event, frame_lower12bit, frame_higher12bit, frame, hexframe;
  uint32_t  checksum_lower12bit, checksum_higher12bit, checksum;
  uint16_t sample, sample_lower8bits, sample_higher4bits, triggerframe_4bits;
  
  if (argc != 4) {
        std::cerr << "Usage: " << argv[0] << " run_number crate_number bin_file_path" << std::endl;
        return 1;
    }

  std::string run_number = argv[1];
  std::string crate_number = argv[2];
  std::string bin_file_path = argv[3];

  std::string output_filename = "run" + run_number + "_crate" + crate_number + ".txt";
  std::ofstream outputFile(output_filename);

  if (!outputFile.is_open()) {
      std::cerr << "ERROR: Could not open output file " << output_filename << std::endl;
      return 1;
  }

  std::ifstream binFile(bin_file_path, std::ios::binary);

  if (!binFile.is_open()) {
      std::cerr << "ERROR: Could not open binary file " << bin_file_path << std::endl;
      return 1;
  }

  while( binFile.peek() != EOF ){
    uint32_t word32b;
    binFile.read( reinterpret_cast<char*>(&word32b), sizeof(word32b) );

    std::cout.setf ( std::ios::hex, std::ios::basefield );  // set hex as the basefield
    std::cout.setf ( std::ios::showbase ); // activate showbase    i.e with prefix 0x

    //    std::cout << "word: " << std::hex << word32b << std::endl;

    uint16_t first16b = word32b & 0xffff; //right 16 bit word
    uint16_t last16b = (word32b>>16) & 0xffff; // left 16 bit word
    if(word32b == 0xffffffff) {
      femHdrCount=1;
      //countheader=true;
      lookupFEM=true;
      cout << "Start of event*******************" << endl;
      //std::cout << "FEM hdrcnt 1 : " << femHdrCount << std::endl;
    }
    else if (word32b  == 0xe0000000){
      cout << "End of *******************" << endl;
      countheader=false;
}

    else{
      if(lookupFEM==true){
      if ((last16b >>8 == 0xf1) and (first16b == 0xffff)){ // there is no word which identifies end of header words for first FEM and start of next FEM , so we have to use this way to identify FEM words instead of using femHdrCount==2
        //      std::cout << "FEM word: " << std::hex << word32b << std::endl;
        fem =(last16b&0x1f);
        //std::cout << "FEM number : " << std::hex << fem << std::endl;
        std::cout << "FEM number : " << std::dec << fem << std::endl;
        countheader=true;
        femHdrCount=1;
        lookupFEM=false;
      }}
      if(countheader==true){
        femHdrCount+=1;
        // std::cout << "FEM hdrcnt: " << femHdrCount << std::endl;
       //       femHdrCount+=1;
       //       std::cout << "FEM hdrcnt: " << femHdrCount << std::endl;
        // if (femHdrCount==3){
         //      femHdrCount+=1;
         // std::cout << "Don't need this word" << word32b <<  " and fem counter: " << femHdrCount << std::endl;
        //}

       if (femHdrCount==4){
         //      femHdrCount+=1;
         //std::cout << "event word: " << std::hex << word32b<<  " and fem counter: " << femHdrCount  << std::endl;
        //      std::cout << "first16b " << std::hex << first16b << " , last: " << last16b << std::endl;
        event_lower12bit= (last16b & 0xfff);
        event_higher12bit= (first16b & 0xfff);
        event = event_higher12bit<<12|event_lower12bit ;
        //std::cout << "first16b " << std::hex << first16b << " msb: " << event_higher12bit << std::endl;
        //      std::cout << "last16b " << std::hex << last16b << "lsb: " << event_lower12bit << std::endl;
        std::cout << "event: " << std::dec << event << std::endl;
}
      else if(femHdrCount==5){
        //      femHdrCount+=1;
        //std::cout << "frame word: " <<  std::hex << word32b <<  " and fem counter: " << femHdrCount  << std::endl;
        //std::cout << "first16b " << std::hex <<first16b << " , last: "<< last16b << std::endl;
        frame_lower12bit= (last16b & 0xfff);
        frame_higher12bit= (first16b & 0xfff);
        hexframe = frame_higher12bit<<12|frame_lower12bit ;
        frame = frame_higher12bit<<12|frame_lower12bit ;

        //std::cout << "hex frame: " << hexframe << std::endl;

        //      std::cout << frame_lower12bit << std::endl;
                std::cout << "FEM frame: " << std::dec << hexframe<< std::endl;

      }

      else if(femHdrCount==7){
        //std::cout << "trigger frame word: " << word32b <<  " and fem counter: " << femHdrCount  << std::endl;
        //std::cout <<  "sample first16b " << std::hex <<first16b << " , last: "<< last16b << std::endl;
        sample_lower8bits = last16b & 0xFF;
        sample_higher4bits = first16b & 0xF;
        triggerframe_4bits = (first16b>>4 & 0xF);
        //      std::cout <<"trigger frame  4-bits: " <<  std::hex << triggerframe_4bits << std::endl;
        //      std::cout << "hex frame: " << std::hex << frame << std::endl;

        frame &= ~0xf; //removing lower 4-bits
        frame |= (triggerframe_4bits & 0xf); //adding 4-bits from trig frame number to get a new trigger frame
        //      std::cout << "Trigger Frame: " << std::hex << frame << std::endl;
        //std::cout << "Trigger Frame: " << std::dec << frame << std::endl;

        /*
        frameCheck = (std::abs(frame - hexframe) > 3) ? (frame - std::pow(2, 3)) : frame;
        std::cout << "Rollover accounted Frame: " << std::dec << frameCheck << std::endl;

        if ((frameCheck - hexframe) < 0) {
          frame = frameCheck + 16;
          std::cout << "(1)Frame is: " << frame << std::endl;
        } else {
          frame = frameCheck;
          std::cout << "(2)Frame is: " << frame <<std::endl;
        }
        */
        if(std::abs(frame-hexframe)>3) {

          frame= frame-8;
          std::cout << "Rollover accounted Frame: " << std::dec << frame << std::endl;
          std::cout << "Diff is:" << std::abs(frame-hexframe) << std::endl;
          if(frame-hexframe<0){
           frame = frame+16;
          std::cout << "Rollover accounted Frame (2nd check: " << std::dec << frame << std::endl;

        }  }
        else{
          frame=frame;
          std::cout << "Frame: " << std::dec << frame << std::endl;

        }
        //      std::cout << sample_higher4bits << "\t" << sample_lower8bits << std::endl;
        sample =sample_higher4bits<<8|sample_lower8bits; //  ((first16b >>4) & 0xF);
        //std::cout << "sample: " << sample << std::endl;
        std::cout << "sample: " << std::dec <<  sample << std::endl;

        //      triggerframe_4bits = (first16b>>4 & 0x0F);
        //      std::cout <<"trigger frame: " <<  triggerframe_4bits << std::endl;

        outputFile << fem << " \t" << event << " \t" << frame <<  " \t" << sample << " \n";


        //      outputFile1 << fem << " \t" << event << " \t" << frame <<  " \t" << frame_lower12bit <<   " \t" << sample << "\t" << hexframe << " \n"; 
        outputFile.flush();
        femHdrCount=-1;
        countheader=false;
        lookupFEM=true;
      }
      }

     else{
       //       femHdrCount=1;
       continue;
     }

    }//end of else

  }//end of while loop
}// end of int main function
