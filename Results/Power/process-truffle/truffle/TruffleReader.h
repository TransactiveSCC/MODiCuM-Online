#include "DIRECTORY TO READER.H"
#include <vector>

class TruffleReader : private Reader {
    public:
        TruffleReader(std::string input, std::string output, std::string directory);
        void processFiles(std::ifstream& infile, std::ofstream& outfile);
};