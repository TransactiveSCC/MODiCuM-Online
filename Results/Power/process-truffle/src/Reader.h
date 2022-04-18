#include <string>
#include <fstream>
#include <iostream>
class Reader {
    public:
        std::string input;
        std::string output;
        std::string directory;
        void openFiles(std::ifstream& infile, std::ofstream& outfile) {
            infile.open("\\" + directory + "Input\\" + input);
            outfile.open(directory + "Output\\" + output);
            if(!infile.is_open()) {
                throw std::runtime_error("Infile not open");
            }
            if(!outfile.is_open()) {
                throw std::runtime_error("Outfile not open");
            }
        }
        Reader(std::string& _input, std::string& _output, std::string& _directory):
            input(_input), output(_output), directory(_directory)
        {}
};