#include <iostream>
#include <gurobi_c++.h>

int main(int argc, char* argv[])
{
    try {
        // Create an environment
        GRBEnv env = GRBEnv();

        // Create a model
        GRBModel model = GRBModel(env);

        // Create variables
        GRBVar x1 = model.addVar(0.0, GRB_INFINITY, 0.0, GRB_CONTINUOUS, "x1");
        GRBVar x2 = model.addVar(0.0, GRB_INFINITY, 0.0, GRB_CONTINUOUS, "x2");

        // Set objective function
        GRBLinExpr obj = 3 * x1 + 4 * x2;
        model.setObjective(obj, GRB_MAXIMIZE);

        // Add constraints
        GRBLinExpr lhs1 = 2 * x1 + x2;
        model.addConstr(lhs1 <= 5, "c1");

        GRBLinExpr lhs2 = x1 + 2 * x2;
        model.addConstr(lhs2 <= 4, "c2");

        // Optimize the model
        model.optimize();

        // Print the optimal solution
        std::cout << "Optimal solution: x1 = " << x1.get(GRB_DoubleAttr_X)
            << ", x2 = " << x2.get(GRB_DoubleAttr_X) << std::endl;

    }
    catch (GRBException e) {
        std::cout << "Error code = " << e.getErrorCode() << std::endl;
        std::cout << e.getMessage() << std::endl;
    }

    return 0;
}