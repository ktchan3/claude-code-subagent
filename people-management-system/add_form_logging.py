#!/usr/bin/env python3
"""
Add debug logging to PersonForm to track data flow.
"""

import os

# Read the person_form.py file
form_file = "client/ui/widgets/person_form.py"

print(f"Adding debug logging to {form_file}")

# Find get_form_data and add logging
with open(form_file, 'r') as f:
    lines = f.readlines()

# Find the get_form_data method
modified = False
for i, line in enumerate(lines):
    if "def get_form_data(self)" in line:
        # Find the return statement
        for j in range(i, min(i+50, len(lines))):
            if "return data" in lines[j]:
                # Add logging before return
                indent = "        "
                logging_code = [
                    f"{indent}# Debug logging\n",
                    f"{indent}logger.info('=== FORM DATA BEING SENT ===')\n",
                    f"{indent}logger.info(f'First Name: {{data.get(\"first_name\")}}')\n",
                    f"{indent}logger.info(f'Last Name: {{data.get(\"last_name\")}}')\n",
                    f"{indent}logger.info(f'Title: {{data.get(\"title\")}}')\n",
                    f"{indent}logger.info(f'Suffix: {{data.get(\"suffix\")}}')\n",
                    f"{indent}logger.info(f'Email: {{data.get(\"email\")}}')\n",
                    f"{indent}logger.info('==========================')\n",
                    f"{indent}\n"
                ]
                
                # Insert logging code before return
                lines[j:j] = logging_code
                modified = True
                print(f"✅ Added logging to get_form_data at line {j}")
                break
        break

# Find set_form_data and add logging
for i, line in enumerate(lines):
    if "def set_form_data(self, data: Dict" in line:
        # Add logging at the start of the method
        indent = "        "
        logging_code = [
            f"{indent}# Debug logging\n",
            f"{indent}logger.info('=== FORM DATA BEING SET ===')\n",
            f"{indent}logger.info(f'First Name: {{data.get(\"first_name\")}}')\n",
            f"{indent}logger.info(f'Last Name: {{data.get(\"last_name\")}}')\n",
            f"{indent}logger.info(f'Title: {{data.get(\"title\")}}')\n",
            f"{indent}logger.info(f'Suffix: {{data.get(\"suffix\")}}')\n",
            f"{indent}logger.info(f'Email: {{data.get(\"email\")}}')\n",
            f"{indent}logger.info('==========================')\n",
            f"{indent}\n"
        ]
        
        # Find the line after the docstring
        for j in range(i+1, min(i+10, len(lines))):
            if '"""' in lines[j] and j > i+1:
                # Insert after docstring
                lines[j+1:j+1] = logging_code
                modified = True
                print(f"✅ Added logging to set_form_data at line {j+1}")
                break
        break

if modified:
    # Write back the modified file
    with open(form_file, 'w') as f:
        f.writelines(lines)
    print(f"\n✅ Successfully added debug logging to {form_file}")
    print("\nNow when you run the client:")
    print("1. Open the Add Person dialog")
    print("2. Fill in First Name, Last Name, Title, Suffix")
    print("3. Save the person")
    print("4. Check the logs to see what data is being sent")
    print("\nThe logs will show:")
    print("  - What data the form is sending")
    print("  - What data the form receives when loading a person")
else:
    print(f"❌ Could not modify {form_file}")