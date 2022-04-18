#include "<DIRECTORY TO TRUFFLE.H>"

int main() {
    std::string input = "truffle.log";
    std::string output = "truffleProcessed.txt";
    std::string directory = "<DIRECTORY TO ALL FILES>";

    TruffleReader truffle(input, output, directory);
    std::ifstream infile;
    std::ofstream outfile;

    std::vector<std::pair<std::string, std::string>> times;
   
    truffle.processFiles(infile, outfile);

    infile.close();
    outfile.close();
    
    return 0;
}