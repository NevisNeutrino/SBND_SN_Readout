void NevisTPCFEM::fem_setup(fhicl::ParameterSet const& crateConfig){
    TLOG(TLVL_INFO) << "FEM setup for slot " << (int)_slot_number;

    // Power On arria power supply
    powerOnArriaFPGA();
    // config on stratix fpga
    configOnStratixFPGA();
    // program stratix firmware
    programStratixFPGAFirmware(crateConfig.get<std::string>("fem_fpga",""));
    TLOG(TLVL_INFO)<<crateConfig.get<std::string>("fem_fpga","") ;

    // Turn DRAM reset on
    resetDRAM(1);
    // Turn DRAM reset off
    resetDRAM(0);
    
    // Set module number
    setModuleNumber(_slot_number);

    // Set compression
    //set whether you want to use huffman compression (mb_feb_a_nocomp)
    //0 for use compression, 1 for don't use compression
    disableNUChanCompression(!( crateConfig.get<bool>( "nu_compress", false ))); //default off
    disableSNChanCompression(!( crateConfig.get<bool>( "sn_compress", true )));
    
    //set mb_feb_timesize
    setDriftTimeSize( crateConfig.get<uint32_t>("timesize",3199) );
    
    //set mb_feb_b_id to chip3
    setSNChannelID(0xf);
    //set mb_feb_b_id to chip4 //???there is no chip4?
    //going to guess this is what was meant
    setNUChannelID(0xf);
    
    //set mb_feb_max to 8000
    setPrebufferSize(8000);
    
    //set mb_feb_hold_enable
    enableLinkPortHold(1);
    
    // Zero suppression configuration
    fhicl::ParameterSet zsParams = crateConfig.get<fhicl::ParameterSet>("zero_suppression_params");
    const std::vector<unsigned int> threshold = zsParams.get<std::vector<unsigned int>>("threshold");
    const std::vector<unsigned int> polarity = zsParams.get<std::vector<unsigned int>>("polarity");
    const std::vector<unsigned int> baseline = zsParams.get<std::vector<unsigned int>>("baseline");

    for (unsigned int chan_it = 0; chan_it < threshold.size(); ++chan_it) {
        if ( baseline.size() == 0 ) { // dynamic baseline
            if (polarity[chan_it] < 1 || polarity[chan_it] > 3) {
                TLOG(TLVL_ERROR) << "Error! Polarity should be 1, 2 or 3 - but it is " << polarity[chan_it] << "! Exiting...";
                exit(1);
            }
            unsigned int i = (polarity[chan_it] << 12) + threshold[chan_it];
            setLoadThreshold( chan_it, i );
        }
        else { // static baseline
            setLoadThreshold( chan_it, (threshold[chan_it] & 0xFFFF) ); // channelwise polarity not supported
            setLoadBaseline( chan_it, (baseline[chan_it] & 0xFFFF) );
        }
    }

    setLoadThresholdMean( zsParams.get<int>( "load_threshold_mean", 0 ));
    setLoadThresholdVariance( zsParams.get<int> ("load_threshold_variance", 0 ));
    setLoadPresample( zsParams.get<int>( "presample", 7 ));
    setLoadPostsample( zsParams.get<int>( "postsample", 7 ));
    setChannelThreshold( zsParams.get<bool>( "channel_threshold", true ));
    if( baseline.size() != 0 ) setFEMBipolar( 2 ); // all bipolar since channelwise polarity not supported

    // Fake data configuration
    bool use_fake_data = crateConfig.get<bool>("fem_fake_data", false);
    enableFEMFakeData( use_fake_data );
    if( use_fake_data ){
        loadFEMFakeData( crateConfig.get<std::string>( "fem_fake_data_pattern", "channel" ) );
    }
}