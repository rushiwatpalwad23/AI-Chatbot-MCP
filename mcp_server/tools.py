from typing import Dict, Any
import random
from web_search import get_web_summary

class CalculatorTool:
    """Calculator tool for basic arithmetic operations"""
    
    def execute(self, params: Dict[str, Any]) -> str:
        try:
            operation = params.get("operation", "").lower().strip()
            a = float(params.get("a", 0))
            b = float(params.get("b", 0))
            
            print(f"🧮 Calculator: {a} {operation} {b}")
            
            if operation == "add":
                result = a + b
                return f"The result of {a} + {b} = {result}"
            elif operation == "subtract":
                result = a - b
                return f"The result of {a} - {b} = {result}"
            elif operation == "multiply":
                result = a * b
                return f"The result of {a} × {b} = {result}"
            elif operation == "divide":
                if b == 0:
                    return "Error: Cannot divide by zero"
                result = a / b
                return f"The result of {a} ÷ {b} = {result}"
            else:
                return f"Error: Unknown operation '{operation}'. Supported operations: add, subtract, multiply, divide"
            
        except ValueError as e:
            return f"Error: Invalid number format - {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"

class TemperatureTool:
    """Temperature tool for getting weather information"""
    
    def execute(self, params: Dict[str, Any]) -> str:
        try:
            # Handle different parameter names
            place_name = (params.get("place_name") or 
                         params.get("place") or 
                         params.get("location") or 
                         params.get("city"))
            
            if not place_name:
                return "Error: No place name provided. Please specify a city name."
            
            print(f"🌡️ Getting temperature for: {place_name}")
            
            # Simulated temperature data with realistic variations
            base_temperatures = {
                # Indian cities
                "pune": 28, "mumbai": 32, "delhi": 25, "bangalore": 22,
                "chennai": 34, "kolkata": 29, "hyderabad": 30, "ahmedabad": 31,
                "jaipur": 27, "lucknow": 26, "kochi": 30, "bhopal": 24,
                
                # International cities
                "london": 15, "new york": 12, "tokyo": 18, "paris": 16,
                "sydney": 24, "dubai": 35, "singapore": 30, "bangkok": 33,
                "moscow": 5, "beijing": 20, "toronto": 8, "berlin": 14
            }
            
            weather_conditions = [
                "Sunny", "Partly cloudy", "Clear sky", "Pleasant", 
                "Warm", "Hot", "Cool", "Mild", "Humid", "Dry"
            ]
            
            place_lower = place_name.lower().strip()
            
            if place_lower in base_temperatures:
                # Add some random variation (-3 to +3 degrees)
                base_temp = base_temperatures[place_lower]
                # actual_temp = base_temp + random.randint(-3, 3)
                actual_temp = base_temp
                condition = random.choice(weather_conditions)
                
                return f"Current temperature in {place_name.title()}: {actual_temp}°C ({condition})"
            else:
                # Default temperature for unknown cities
                default_temp = random.randint(20, 30)
                condition = random.choice(weather_conditions)
                return f"Current temperature in {place_name.title()}: {default_temp}°C ({condition}) - Estimated data"
            
        except Exception as e:
            return f"Error getting temperature: {str(e)}"


class GeminiWebSearchTool:
    """Gemini-powered web search tool for real-time information and to get latest updates."""
    
    def __init__(self):
        self.max_content_length = 2000  # Limit content to fit context window
    
    def truncate_content(self, content: str, max_length: int = None) -> str:
        """Truncate content to fit within context window limits"""
        if max_length is None:
            max_length = self.max_content_length
        
        if len(content) <= max_length:
            return content
        
        # Try to truncate at sentence boundary
        truncated = content[:max_length]
        last_period = truncated.rfind('.')
        last_exclamation = truncated.rfind('!')
        last_question = truncated.rfind('?')
        
        last_sentence_end = max(last_period, last_exclamation, last_question)
        
        if last_sentence_end > max_length * 0.8:  # If we found a good ending point
            truncated = truncated[:last_sentence_end + 1]
        
        truncated += f"\n\n[Content truncated for context window - showing first {len(truncated)} of {len(content)} characters]"
        return truncated
    
    def execute(self, params: Dict[str, Any]) -> str:
        try:
            query = params.get("query") or params.get("question") or params.get("search_query")
            max_length = params.get("max_length", "medium")
            
            if not query:
                return "Error: No search query provided. Please specify what you want to search for."
            
            print(f"🔍 Gemini Web Search for: {query}")
            
            # Set content length based on parameter
            if max_length == "short":
                content_limit = 1000
            elif max_length == "long":
                content_limit = 3000
            else:  # medium
                content_limit = 2000
            
            # Call the Gemini search function
            try:
                search_result = get_web_summary(query)
                
                if not search_result or search_result == "No answer received.":
                    return f"Error: Could not retrieve search results for '{query}'. The Gemini search service may be unavailable."
                
                # Truncate if necessary
                final_result = self.truncate_content(search_result, content_limit)
                
                print(f"✅ Gemini search completed: {len(final_result)} characters returned")
                
                return f"Latest web search results for '{query}':\n\n{final_result}"
                
            except Exception as search_error:
                print(f"❌ Gemini search error: {str(search_error)}")
                return f"Error: Gemini web search failed for '{query}': {str(search_error)}"
            
        except Exception as e:
            return f"Error during web search: {str(e)}"