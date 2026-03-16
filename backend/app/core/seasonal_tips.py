"""
Seasonal Tips - Provides time-relevant advice for coffee farmers
"""

import json
from datetime import datetime
from typing import Dict, List, Optional


class SeasonalRecommendations:
    """
    Provides seasonal tips based on the current time of year
    """
    
    def __init__(self):
        # Define seasons for Kenya (coffee growing regions)
        # Long rains: March - May
        # Short rains: October - December
        # Main harvest: October - February
        # Fly crop: June - September
        
        self.seasonal_data = {
            'march': {
                'en': {
                    'season': 'Long Rains Beginning',
                    'tip': '🌧️ This is the start of long rains. Apply fertilizer now for best absorption.',
                    'activities': ['Fertilizer application', 'Weeding', 'Pruning']
                },
                'ki': {
                    'season': 'Mĩgĩ ya Gĩthũngũ Ĩrĩa Kũrĩa',
                    'tip': '🌧️ Ũno nĩ thutha wa mĩgĩ ya gĩthũngũ. Ikĩra mboleo rĩu no kwega.',
                    'activities': ['Kwĩkĩra mboleo', 'Kũhũa', 'Gũceha']
                }
            },
            'april': {
                'en': {
                    'season': 'Peak Long Rains',
                    'tip': '🌧️ Heavy rains expected. Check drainage to prevent root rot.',
                    'activities': ['Disease monitoring', 'Mulching', 'Pest control']
                },
                'ki': {
                    'season': 'Mĩgĩ Mĩnene',
                    'tip': '🌧️ Mĩgĩ ĩrĩ mĩnene. Rĩka mũhũmũ wa maaĩ nĩguo root rot ĩngĩa.',
                    'activities': ['Kũrora mĩrimũ', 'Kũthũka', 'Kũrora tũtambi']
                }
            },
            'may': {
                'en': {
                    'season': 'Long Rains Ending',
                    'tip': '🌧️ Rains ending. Apply final fertilizer application for the season.',
                    'activities': ['Final fertilizer', 'Harvest preparation', 'Nursery planting']
                },
                'ki': {
                    'season': 'Mĩgĩ ya Gĩthũngũ Ĩrĩa Gũtherera',
                    'tip': '🌧️ Mĩgĩ ĩgũthera. Ikĩra mboleo wa mũgĩria kũrĩa kũrĩa.',
                    'activities': ['Mboleo wa mũgĩria', 'Kũrĩa kũgetha', 'Kũhanda nathari']
                }
            },
            'june': {
                'en': {
                    'season': 'Fly Crop Season',
                    'tip': '☀️ Dry season begins. Coffee trees need careful watering.',
                    'activities': ['Irrigation', 'Shade management', 'Pest monitoring']
                },
                'ki': {
                    'season': 'Kĩrĩma Gitũ',
                    'tip': '☀️ Mũthĩ nĩ ũrĩa. Mĩtĩ ya kahũa ĩkĩbatĩra maaĩ.',
                    'activities': ['Kũrĩa maaĩ', 'Kũrora mũcengi', 'Kũrora tũtambi']
                }
            },
            'july': {
                'en': {
                    'season': 'Dry Season',
                    'tip': '☀️ Continue irrigation. Watch for pests during dry weather.',
                    'activities': ['Regular irrigation', 'Pest control', 'Pruning']
                },
                'ki': {
                    'season': 'Mũthĩ',
                    'tip': '☀️ Rĩka kũrĩa maaĩ. Rora tũtambi mũthĩ-inĩ.',
                    'activities': ['Kũrĩa maaĩ', 'Kũrora tũtambi', 'Gũceha']
                }
            },
            'august': {
                'en': {
                    'season': 'Dry Season',
                    'tip': '☀️ Peak dry season. Mulch heavily to retain moisture.',
                    'activities': ['Heavy mulching', 'Water conservation', 'Flowering begins']
                },
                'ki': {
                    'season': 'Mũthĩ',
                    'tip': '☀️ Mũthĩ mũkũrũ. Thũka mũno nĩguo ithĩke.',
                    'activities': ['Kũthũka mũno', 'Kũrora maaĩ', 'Kũrĩa mbĩ']
                }
            },
            'september': {
                'en': {
                    'season': 'Flowering Period',
                    'tip': '🌸 Coffee is flowering. Avoid spraying during this time.',
                    'activities': ['Avoid spraying', 'Irrigation', 'Pollinator protection']
                },
                'ki': {
                    'season': 'Kũrĩa Mbĩ',
                    'tip': '🌸 Kahũa kĩrĩa mbĩ. Ndũkahe dawa hĩndĩ ĩno.',
                    'activities': ['Ndũkahe dawa', 'Kũrĩa maaĩ', 'Kũrora atĩrĩ']
                }
            },
            'october': {
                'en': {
                    'season': 'Short Rains Beginning',
                    'tip': '🌧️ Short rains starting. Apply top-dressing fertilizer now.',
                    'activities': ['Top-dressing', 'Weeding', 'Harvest begins']
                },
                'ki': {
                    'season': 'Mĩgĩ ya Mũthĩ Ĩrĩa Kũrĩa',
                    'tip': '🌧️ Mĩgĩ ya mũthĩ ĩrĩa kũrĩa. Ikĩra mboleo wa top-dress rĩu.',
                    'activities': ['Top-dress', 'Kũhũa', 'Kũgetha gĩtĩria']
                }
            },
            'november': {
                'en': {
                    'season': 'Main Harvest',
                    'tip': '🧺 Peak harvest season. Pick cherries when fully red.',
                    'activities': ['Harvesting', 'Processing', 'Quality control']
                },
                'ki': {
                    'season': 'Kũgetha Gĩtĩria',
                    'tip': '🧺 Kĩrĩma gia kũgetha. Getha mbegũ rĩrĩa ĩtuĩka njirũ.',
                    'activities': ['Kũgetha', 'Gũthondeka', 'Kũrora mũcamo']
                }
            },
            'december': {
                'en': {
                    'season': 'Main Harvest',
                    'tip': '🧺 Continue harvesting. Process cherries the same day.',
                    'activities': ['Harvesting', 'Pulping', 'Fermentation']
                },
                'ki': {
                    'season': 'Kũgetha Gĩtĩria',
                    'tip': '🧺 Rĩka kũgetha. Thondeka mbegũ o rũmwe wiathi.',
                    'activities': ['Kũgetha', 'Kũcukia', 'Kũthũka']
                }
            },
            'january': {
                'en': {
                    'season': 'Main Harvest',
                    'tip': '🧺 End of main harvest. Ensure proper drying of parchment.',
                    'activities': ['Final harvest', 'Drying', 'Storage']
                },
                'ki': {
                    'season': 'Kũgetha Gĩtĩria',
                    'tip': '🧺 Ngoro ya kũgetha. Rĩka kũũma kahũa.',
                    'activities': ['Kũgetha wa mũgĩria', 'Kũũma', 'Kũrĩa']
                }
            },
            'february': {
                'en': {
                    'season': 'Post-Harvest',
                    'tip': '🌱 Post-harvest period. Prune and prepare for new season.',
                    'activities': ['Pruning', 'Field preparation', 'Nursery preparation']
                },
                'ki': {
                    'season': 'Thutha wa Kũgetha',
                    'tip': '🌱 Thutha wa kũgetha. Ceha na kũrĩa kũhanda.',
                    'activities': ['Gũceha', 'Kũrĩa irima', 'Kũrĩa nathari']
                }
            }
        }
        
        # Emergency alerts
        self.emergency_alerts = {
            'cbd': {
                'en': '🚨 CBD ALERT: Coffee Berry Disease risk is HIGH during wet seasons. Spray copper fungicide now!',
                'ki': '🚨 CBD: Gĩtĩna gia CBD nĩ gĩkũrũ hĩndĩ ya mĩgĩ. Haka dawa ya copper rĩu!'
            },
            'rust': {
                'en': '🚨 RUST ALERT: Coffee Leaf Rust reported in some areas. Check leaves for orange spots!',
                'ki': '🚨 RUST: CLR ĩrĩo ũrĩa mĩtĩni. Rora mathangũ ma machungwa!'
            }
        }
    
    def get_current_month(self) -> str:
        """Get current month name"""
        month = datetime.now().month
        months = ['january', 'february', 'march', 'april', 'may', 'june',
                  'july', 'august', 'september', 'october', 'november', 'december']
        return months[month - 1]
    
    def get_current_tips(self, language: str = 'en') -> Dict:
        """
        Get current seasonal tips
        """
        month = self.get_current_month()
        return self.seasonal_data.get(month, {}).get(language, self.seasonal_data.get(month, {}).get('en', {}))
    
    def get_tips_for_month(self, month: str, language: str = 'en') -> Dict:
        """
        Get tips for a specific month
        """
        return self.seasonal_data.get(month.lower(), {}).get(language, {})
    
    def get_emergency_alert(self, alert_type: str, language: str = 'en') -> Optional[str]:
        """
        Get emergency alert if any
        """
        return self.emergency_alerts.get(alert_type.lower(), {}).get(language)
    
    def get_year_calendar(self, language: str = 'en') -> Dict:
        """
        Get full year calendar with tips
        """
        return {
            month: self.seasonal_data.get(month, {}).get(language, {})
            for month in ['january', 'february', 'march', 'april', 'may', 'june',
                          'july', 'august', 'september', 'october', 'november', 'december']
        }
    
    def get_activities_for_month(self, month: str) -> List[str]:
        """
        Get list of activities for a month
        """
        data = self.seasonal_data.get(month.lower(), {})
        en_data = data.get('en', {})
        return en_data.get('activities', [])
    
    def is_peak_harvest(self) -> bool:
        """Check if currently in peak harvest season"""
        month = self.get_current_month()
        return month in ['october', 'november', 'december', 'january']
    
    def is_rainy_season(self) -> bool:
        """Check if currently in rainy season"""
        month = self.get_current_month()
        return month in ['march', 'april', 'may', 'october', 'november', 'december']
