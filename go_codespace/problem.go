import (
	"fmt"
	"io"
	"os"
	"path/filepath"
)


type Event struct
{
	features:= []int{}
	students:=[]int{}
}

type Room struct
{
	capacity int
	features:=[]int{}
}


type Problem struct
{
	var path_to_problem=filepath.Join(".","instances")
	var events=[]Event{}
	var rooms=[]Event{}
	var students=make(map[int]int)
	var E int
	var S int
	var R int
	P:=45
}

func check(e error)
{
	if e!=nil{
		panic(e)
	}
}

func (p Problem) read(filename string)
{
	filr,err=os.Open(filepath.Join(p.path_to_problem,filename))
	if err!=nil{
		fmt.Println("Error in opening file:",err)
		return
	}
	deref file.Close()

	filestart:=true
	scanner:=bufio.NewScanner(file)
	for scanner.Scan(){
		if filestart{
			data=strings.Spilt(scanner.Text()," ")

		}
	}
}