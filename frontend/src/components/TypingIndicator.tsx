import React from 'react';

const TypingIndicator: React.FC = () => {
  return (
    <div className="flex items-center space-x-1">
      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce-dot"></div>
      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce-dot animation-delay-200"></div>
      <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce-dot animation-delay-400"></div>
    </div>
  );
};

export default TypingIndicator;

// Tailwind CSS keyframes and animation classes
// Add the following to your Tailwind CSS configuration (tailwind.config.js):
// module.exports = {
//   theme: {
//     extend: {
//       keyframes: {
//         bounceDot: {
//           '0%, 80%, 100%': { transform: 'scale(0)' },
//           '40%': { transform: 'scale(1)' },
//         },
//       },
//       animation: {
//         'bounce-dot': 'bounceDot 1.4s infinite',
//       },
//     },
//   },
//   plugins: [],
// };