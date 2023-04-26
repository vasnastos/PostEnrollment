### Install gurobi for C++ in visual studio

* Right-click on the project name in the Solution Explorer panel, then select Properties.

* Set Platform to x64

* Set Configuration to All Configurations

    ![./Figures/step0.png](./Figures/step0.png)

* Under Debugging set Environment to PATH=$(PATH);$(GUROBI_HOME)\lib
    
    ![./Figures/step1.png](./Figures/step1.png)

* Under C/C++ > General > Additional Include Directories, add: $(GUROBI_HOME)\include
    
    ![./Figures/step2.png](./Figures/step2.png)

* Under C/C++ > Precompiled Headers > Precompiled Header, select Not Using Precompiled Headers
    
    ![./Figures/step3.png](./Figures/step3.png)

* Under Linker > General > Additional Library Directories, add: $(GUROBI_HOME)\lib
    
    ![./Figures/step4.png](./Figures/step4.png)

* Set Configuration to Debug

* Under Linker > Input > Additional Dependencies, add gurobi100.lib; gurobi_c++mdd2017.lib
    
    ![./Figures/step5.png](./Figures/step5.png)

* Set Configuration to Release

* Under Linker > Input > Additional Dependencies, add gurobi100.lib; gurobi_c++md2017.lib
  
    ![./Figures/step6.png](./Figures/step6.png)


**When building your project, make sure the current target in the Visual Studio toolbar is x64 (it usually defaults to x86).**