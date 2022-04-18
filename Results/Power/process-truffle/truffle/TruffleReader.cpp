#include "<DIRECTORY TO TRUFFLEREADER.H>"
#include <time.h>

TruffleReader::TruffleReader(std::string input, std::string output, std::string directory):
    Reader(input, output, directory)
{
}

void TruffleReader::processFiles(std::ifstream& infile, std::ofstream& outfile) {
    openFiles(infile, outfile);

    std::string line;
    std::string lastBlock;

    while(std::getline(infile, line)) {
        std::size_t method = line.find("Method: ");
        std::size_t atEnd = line.find("End Time:");
        std::size_t blockNum = line.find("blockNumber: ");
        std::size_t blockDifficulty = line.find("difficulty: ");

        if(method != std::string::npos) {
            std::size_t timeStart = line.find("Start Time:");
            outfile << line << "\n";
        }

        if(blockNum != std::string::npos) {
            std::string l = "blockNumber: [33m";
            std::size_t startPos = line.find("[");
            std::size_t endPos = line.find("[", l.length() + 3);

            lastBlock = line.substr(l.length(), endPos - 10); // Requires post processing
        }

        if(blockDifficulty != std::string::npos) {
            std::string l = "difficulty:  [32m'";
            std::size_t endPos = line.find("'", l.size());

            std::string fin = line.substr(l.length() + 2, endPos - 7);
            
            outfile << "Block:\t" << lastBlock  << "\t" << fin << "\n"; // Requires post processing
        }

        if(atEnd != std::string::npos) {
            outfile << line << "\n"; // Outputs end time
            std::size_t timeStart = line.find("1");
            std::getline(infile, line);
            outfile << line << "\n";
        }
    }
}