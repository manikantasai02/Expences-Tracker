#include <stdio.h>
#include <stdlib.h> // Needed for the exit() function

int main()
{
    int n;
    int Food = 0, Cloths = 0, Medical = 0, Enjoyment = 0, Fees = 0, Travelling = 0;
    int choice;

    printf("Enter your expense amount: ");
    if (scanf("%d", &n) != 1) {
        printf("Invalid input.\n");
        return 1;
    }

    printf("\n1. Food\n2. Cloths\n3. Medical\n4. Enjoyment\n5. Fees\n6. Travelling\n7. Exit\n\n");
    printf("Enter your choice (1-7): ");
    scanf("%d", &choice); // Fixed: Added scanf to get the user's choice

    
    switch(choice) {
        case 1:
            Food = n;
            printf("Amount %d added to Food.\n", Food);
            break;
            
        case 2:
            Cloths = n;
            printf("Amount %d added to Cloths.\n", Cloths);
            break;
            
        case 3:
            Medical = n;
            printf("Amount %d added to Medical.\n", Medical);
            break;
            
        case 4:
            Enjoyment = n; // Fixed: Corrected variable mapping
            printf("Amount %d added to Enjoyment.\n", Enjoyment);
            break;
            
        case 5:
            Fees = n; // Fixed: Corrected variable mapping
            printf("Amount %d added to Fees.\n", Fees);
            break;
            
        case 6:
            Travelling = n;
            printf("Amount %d added to Travelling.\n", Travelling);
            break;
            
        case 7:
            printf("Exiting program.\n");
            exit(0); // Fixed: Passed 0 to exit status
            
        default:
            printf("Invalid choice!\n");
            break;
    }

    return 0;
}
