#ifndef DECODER_CHANNEL_NU_H
#define DECODER_CHANNEL_NU_H

#include <cstdint>
#include <vector>

class channelNU {

public:
	// constructor
	channelNU(unsigned short channelStartNum) : channelStartNum_(channelStartNum) {};
	channelNU() {};

	// setters
	void setChannelStartNum(unsigned short channelStartNum) { channelStartNum_ = channelStartNum; }
	void setChannelEndNum(unsigned short channelEndNum) { channelEndNum_ = channelEndNum; }
	void setChannelEndMiss(bool channelEndMiss) { channelEndMiss_ = channelEndMiss; }
	
	// getters
	unsigned short getChannelStartNum() const { return channelStartNum_; }
	unsigned short getChannelEndNum() const { return channelEndNum_; }
	bool getChannelEndMiss() const { return channelEndMiss_; }
	unsigned int getADCCnt() const { return adcs_.size(); }
	const std::vector<unsigned short>& getADCs() const { return adcs_; }
	const std::vector<unsigned short>& getSampleNums() const { return sampleNums_; }

	void pushADC(unsigned short adc);
	void pushSampleNum(unsigned short sampleNum);
	void clearADCs();
	void clearSampleNums();

	// destructor
	~channelNU() {};

protected:

private:
	unsigned short channelStartNum_;
	unsigned short channelEndNum_;
	bool channelEndMiss_;
	std::vector<unsigned short> adcs_;
	std::vector<unsigned short> sampleNums_;

};

#endif //DECODER_CHANNEL_NU_H
